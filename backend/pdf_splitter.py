import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageEnhance

try:
    from paddleocr import PaddleOCR
except Exception:  # pragma: no cover
    PaddleOCR = None


def normalize_text(value: str) -> str:
    text = (value or "").strip().upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


def enhance_image_for_ocr(img_array: np.ndarray) -> np.ndarray:
    """
    Enhance image quality for better OCR:
    - Increase contrast
    - Adjust brightness
    - Convert to PIL, enhance, convert back
    """
    try:
        pil_img = Image.fromarray(img_array.astype('uint8'))
        
        # Enhance contrast (factor > 1.0 = increase contrast)
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(pil_img)
        pil_img = enhancer.enhance(1.3)
        
        # Convert back to numpy
        return np.array(pil_img)
    except Exception:
        # If enhancement fails, return original
        return img_array


def fix_common_ocr_errors(text: str) -> str:
    """Fix common OCR errors specific to Vietnamese text."""
    # Common OCR mistakes in Vietnamese
    fixes = {
        r'\bl\b': 'I',  # 'l' (lowercase L) often misread for 'I'
        r'\bO\b': '0' if len(text) > 0 else 'O',  # Context-dependent
        r's(?=\d)': 'S',  # 's' before numbers should be 'S'
        r'\s+': ' ',  # Normalize spaces
    }
    
    # Apply basic fixes
    result = text
    result = re.sub(r'\bl(?=[\d\-/])', 'I', result)  # l before numbers
    result = re.sub(r'(?<=\s)s(?=\d)', 'S', result)  # Số before numbers
    
    return result.strip()


class DocumentOCR:
    """Extract text lines from PDF pages using text-layer first, OCR fallback second."""

    def __init__(self, use_ocr_fallback: bool = True, lang: str = "vi") -> None:
        self.use_ocr_fallback = use_ocr_fallback
        self.lang = lang
        self._ocr: Optional[Any] = None

    def _get_ocr(self) -> Optional[Any]:
        if not self.use_ocr_fallback or PaddleOCR is None:
            return None
        if self._ocr is None:
            self._ocr = PaddleOCR(use_angle_cls=True, lang=self.lang, show_log=False)
        return self._ocr

    def _extract_from_text_layer(self, page: fitz.Page) -> List[Dict[str, Any]]:
        lines: List[Dict[str, Any]] = []
        text_dict = page.get_text("dict")

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = "".join(span.get("text", "") for span in spans).strip()
                if not text:
                    continue
                x0, y0, x1, y1 = line.get("bbox", (0.0, 0.0, 0.0, 0.0))
                lines.append(
                    {
                        "text": text,
                        "bbox": (float(x0), float(y0), float(x1), float(y1)),
                        "conf": 1.0,
                        "source": "text_layer",
                    }
                )
        return lines

    def _extract_from_ocr(self, page: fitz.Page, zoom: float = 3.0) -> List[Dict[str, Any]]:
        """
        Extract text from page using OCR with image enhancement.
        Higher zoom (3.0) + image enhancement for better accuracy.
        """
        ocr = self._get_ocr()
        if ocr is None:
            return []

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

        # Enhance image for better OCR
        img = enhance_image_for_ocr(img)

        result = ocr.ocr(img, cls=True)
        if not result or not result[0]:
            return []

        sx = page.rect.width / (pix.width / zoom)
        sy = page.rect.height / (pix.height / zoom)
        lines: List[Dict[str, Any]] = []

        for item in result[0]:
            box, payload = item[0], item[1]
            text = (payload[0] or "").strip()
            conf = float(payload[1]) if payload and len(payload) > 1 else 0.0
            
            # Apply OCR error fixes
            text = fix_common_ocr_errors(text)
            
            if not text:
                continue

            # Include OCR results with confidence >= 0.5 (not just >= 0.6)
            # This allows detecting important keywords even if OCR confidence is lower
            if conf < 0.5:
                continue

            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)

            lines.append(
                {
                    "text": text,
                    "bbox": (x0 * sx, y0 * sy, x1 * sx, y1 * sy),
                    "conf": conf,
                    "source": "ocr",
                }
            )

        return lines

    def extract_page_lines(self, page: fitz.Page) -> Dict[str, Any]:
        text_raw = page.get_text("text") or ""
        has_text_layer = len(text_raw.strip()) >= 20

        if has_text_layer:
            text_lines = self._extract_from_text_layer(page)
            if text_lines:
                return {
                    "lines": text_lines,
                    "source": "text_layer",
                    "text_preview": text_raw.strip().replace("\n", " ")[:280],
                    "avg_confidence": 1.0,
                }

        ocr_lines = self._extract_from_ocr(page)
        preview = " ".join(line["text"] for line in ocr_lines)[:280] if ocr_lines else ""
        avg_conf = float(sum(line["conf"] for line in ocr_lines) / len(ocr_lines)) if ocr_lines else 0.0

        return {
            "lines": ocr_lines,
            "source": "ocr",
            "text_preview": preview,
            "avg_confidence": avg_conf,
        }


class SplitEngine:
    """Detect start pages using 3 anchors and split PDF by selected breaks."""

    TITLE_TYPES = {
        "HUONG DAN",
        "KE HOACH",
        "QUY DINH",
        "THONG BAO",
        "NGHI QUYET",
        "QUYET DINH",
        "GIAY MOI HOI NGHI",  # Invitation letter
        "CHI THI",            # Directive
        "PHUONG CHIEN KINH TE XA HOI",  # Economic-social strategy
        "CHI TIEU",           # Index/criteria
    }

    EMBLEM_PHRASES = {
        "DANG CONG SAN VIET NAM",
        "CONG HOA XA HOI CHU NGHIA VIET NAM",
    }

    DOC_NUMBER_RE = re.compile(r"\bSO\s*:?\s*\d+\s*[-/]\s*[A-Z0-9][A-Z0-9./-]*", re.IGNORECASE)
    DOC_NUMBER_FALLBACK_RE = re.compile(r"\b\d{1,4}\s*[-/]\s*[A-Z0-9]{1,12}(?:\s*/\s*[A-Z0-9.-]{1,12})?", re.IGNORECASE)

    def __init__(self, ocr_reader: Optional[DocumentOCR] = None, start_threshold: float = 1.0) -> None:
        self.ocr_reader = ocr_reader or DocumentOCR(use_ocr_fallback=True, lang="vi")
        self.start_threshold = start_threshold

    @staticmethod
    def _has_token_group(text_norm: str, token_group: List[str], min_hit: int) -> bool:
        hits = 0
        for token in token_group:
            if token in text_norm:
                hits += 1
        return hits >= min_hit

    def _detect_anchor_1_emblem(self, lines: List[Dict[str, Any]], page_height: float) -> bool:
        """
        Detect emblem (Quốc hiệu/Đảng hiệu) in top 42% of page.
        Requires clear evidence of Vietnamese government emblem, not just random keywords.
        """
        top_limit = page_height * 0.42
        top_text_parts: List[str] = []

        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if y1 > top_limit:
                continue

            text_norm = normalize_text(line["text"])
            if not text_norm:
                continue

            top_text_parts.append(text_norm)

            # Check for exact/complete emblem phrases
            if any(phrase in text_norm for phrase in self.EMBLEM_PHRASES):
                return True

            # Fuzzy matching: require minimum evidence of emblem
            # "DANG CONG SAN VIET NAM" or "CONG HOA XA HOI CHU NGHIA VIET NAM"
            if self._has_token_group(text_norm, ["DANG", "CONG SAN", "VIET NAM"], min_hit=2):
                return True
            if self._has_token_group(text_norm, ["CONG HOA", "XA HOI", "CHU NGHIA", "VIET NAM"], min_hit=3):
                return True

        # Combine all top lines to handle multi-line emblems
        combined_top_text = " ".join(top_text_parts)
        
        if not combined_top_text.strip():
            return False

        # For degraded scans: accept if we have solid evidence
        # Require at least 2 key emblem components
        if self._has_token_group(combined_top_text, ["DANG", "CONG SAN", "VIET NAM"], min_hit=2):
            return True
        if self._has_token_group(combined_top_text, ["CONG HOA", "XA HOI", "CHU NGHIA", "VIET NAM"], min_hit=3):
            return True

        # Lenient: if multiple emblem keywords are present in top section
        emblem_keywords = {"DANG", "CONG", "VIET NAM", "HOA", "XA HOI", "CHU NGHIA"}
        keyword_hits = sum(1 for kw in emblem_keywords if kw in combined_top_text)
        
        # Accept only if we have strong evidence (at least 2-3 keywords indicating government emblem)
        if keyword_hits >= 3:
            return True

        return False

    def _detect_anchor_2_doc_number(self, lines: List[Dict[str, Any]], page_width: float, page_height: float) -> str:
        """
        Detect document number (Số hiệu văn bản).
        Requirements:
        - Either: "Số" + number pattern (e.g., "Số 123-AB/CD")
        - Or: Standard doc number format "123-AB/CD" or "123-AB" in top-left area
        - NOT acceptable: random numbers in text like "(... s604-TB/...)" without "Số" prefix
        """
        y_limit = page_height * 0.70
        x_limit = page_width * 0.68

        # Phase 1: Look for standard "Số XX-YY/ZZ" pattern (most reliable)
        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if y0 > y_limit or x0 > x_limit:
                continue

            text = line["text"]
            text_norm = normalize_text(text)
            
            # Primary regex: "Số XX-YY/ZZ"
            match = self.DOC_NUMBER_RE.search(text_norm)
            if match:
                return text.strip()[:120]

        # Phase 2: Look for "Số" + some digits/pattern (lenient for OCR errors)
        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if y0 > y_limit or x0 > x_limit:
                continue

            text = line["text"]
            text_norm = normalize_text(text)

            # Must contain "SO" (Số in Vietnamese)
            if "SO" not in text_norm:
                continue

            # And must have a number pattern after it
            # Pattern: "Số" followed by digits-something
            pattern = r"SO\s*:?\s*\d{1,4}\s*[-/]"
            if re.search(pattern, text_norm):
                return text.strip()[:120]

        # Phase 3: Look in top-left area for cleaner patterns
        # BUT: also check for abbreviated patterns like "SỐ GĐ-TB/DU"
        left_area_x_limit = page_width * 0.50
        top_area_y_limit = page_height * 0.35

        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if x0 > left_area_x_limit or y0 > top_area_y_limit:
                continue

            text = line["text"]
            text_norm = normalize_text(text)

            # Look for patterns with "SO" at start:
            # "SỐ" or "SO" followed by space/colon, then doc number
            # Allows for abbreviated doc numbers like "SỐ GĐ-TB/DU"
            pattern = r"^SO[\s:]?(?:[A-Z]{1,4}[-/][A-Z0-9]{1,8}|[A-Z0-9].*)"
            if re.match(pattern, text_norm):
                return text.strip()[:120]

        # Phase 4: Pure positional heuristic in top-left for standalone numbers
        left_area_x_limit = page_width * 0.45
        top_area_y_limit = page_height * 0.30

        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if x0 > left_area_x_limit or y0 > top_area_y_limit:
                continue

            text = line["text"]
            text_norm = normalize_text(text)

            # STRICT: Pattern must look like a standalone doc number
            # Not acceptable: numbers inside parentheses or narrative text
            # Pattern: NUMBER-LETTER or NUMBER-LETTER/LETTER
            strict_pattern = r"^\d{1,4}\s*[-/]\s*[A-Z0-9]{1,12}(?:\s*/\s*[A-Z0-9.-]{1,8})?$"
            
            if re.match(strict_pattern, text_norm):
                return text.strip()[:120]

        return ""

    def _detect_anchor_3_title(
        self,
        lines: List[Dict[str, Any]],
        page_width: float,
        page_height: float,
    ) -> str:
        """
        Detect document title (Tên loại văn bản).
        Looks for keywords like "THÔNG BÁO", "GIẤY MỜI HỘI NGHỊ", etc.
        Uses multi-pass approach: strict centering → lenient centering → heuristic.
        """
        top_limit = page_height * 0.55
        center_x = page_width / 2.0

        # Phase 1: Strict centering (±25% of page width)
        for line in lines:
            text = (line["text"] or "").strip()
            if not text or len(text) < 3:
                continue

            x0, y0, x1, y1 = line["bbox"]
            if y1 > top_limit:
                continue

            line_center = (x0 + x1) / 2.0
            is_centered = abs(line_center - center_x) <= page_width * 0.25
            if not is_centered:
                continue

            text_norm = normalize_text(text)
            has_title_keyword = any(title in text_norm for title in self.TITLE_TYPES)
            if not has_title_keyword:
                continue

            # Prefer uppercase titles
            alpha_chars = [c for c in text if c.isalpha()]
            is_upper_like = bool(alpha_chars) and text == text.upper()

            # Prefer short, standalone title lines
            word_count = len(text_norm.split())
            looks_standalone = word_count <= 10

            if is_upper_like or looks_standalone:
                return text

        # Phase 2: Lenient centering (±40% of page width)
        lenient_center_tolerance = page_width * 0.40

        for line in lines:
            text = (line["text"] or "").strip()
            if not text or len(text) < 3:
                continue

            x0, y0, x1, y1 = line["bbox"]
            if y1 > top_limit:
                continue

            line_center = (x0 + x1) / 2.0
            is_roughly_centered = abs(line_center - center_x) <= lenient_center_tolerance
            if not is_roughly_centered:
                continue

            text_norm = normalize_text(text)
            has_title_keyword = any(title in text_norm for title in self.TITLE_TYPES)

            if has_title_keyword:
                word_count = len(text_norm.split())
                if word_count <= 15:  # Slightly more lenient
                    return text

        # Phase 3: Partial keyword matching for multi-word titles
        # E.g., "GIAY MOI" might match "GIAY MOI HOI NGHI"
        for line in lines:
            text = (line["text"] or "").strip()
            if not text or len(text) < 3:
                continue

            x0, y0, x1, y1 = line["bbox"]
            if y1 > top_limit:
                continue

            text_norm = normalize_text(text)
            
            # Check for partial matches
            # E.g., if line contains 2+ keywords from multi-word title
            for title in self.TITLE_TYPES:
                title_parts = title.split()
                if len(title_parts) > 1:
                    # For multi-word titles, accept if 2+ keywords present
                    matches = sum(1 for part in title_parts if part in text_norm)
                    if matches >= 2:
                        line_center = (x0 + x1) / 2.0
                        is_vaguely_centered = abs(line_center - center_x) <= page_width * 0.45
                        word_count = len(text_norm.split())
                        
                        if is_vaguely_centered and word_count <= 20:
                            return text

        return ""

    def _is_start_page(self, anchors: List[bool]) -> bool:
        ratio = sum(1 for x in anchors if x) / float(len(anchors))
        return ratio >= self.start_threshold

    @staticmethod
    def _start_score(anchors: List[bool]) -> float:
        if not anchors:
            return 0.0
        return sum(1 for x in anchors if x) / float(len(anchors))

    def _is_low_quality_scan(self, avg_confidence: float, text_preview: str) -> bool:
        """Detect if this page is from a low-quality scan."""
        # If OCR confidence is low (mean conf < 0.85), likely degraded scan
        if avg_confidence < 0.85:
            return True

        # If text preview is very short/empty but it's OCR source, likely poor quality
        if len(text_preview.strip()) < 50:
            return True

        return False

    def _get_effective_threshold(self, avg_confidence: float, text_preview: str, source: str) -> float:
        """
        Determine effective threshold:
        - If user already selected flexible mode (threshold < 1.0): ALWAYS use it, no override
        - If user selected strict mode (threshold = 1.0): auto-adjust if OCR is poor
        """
        # If already in flexible mode (user explicitly chose 2/3), respect their choice
        if self.start_threshold < 1.0:
            return self.start_threshold
        
        # Only auto-adjust if in strict mode (threshold == 1.0)
        # For text-layer PDFs, keep strict threshold
        if source == "text_layer":
            return self.start_threshold
        
        # For OCR sources: auto-adjust from strict (1.0) to flexible (0.67) if quality is poor
        if self._is_low_quality_scan(avg_confidence, text_preview):
            return 0.67
        
        # Otherwise, keep strict threshold
        return self.start_threshold

    def analyze_pdf(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        doc = fitz.open(str(path))
        pages_output: List[Dict[str, Any]] = []
        suggested_breaks: List[int] = [0]

        try:
            for idx in range(len(doc)):
                page = doc[idx]
                w = float(page.rect.width)
                h = float(page.rect.height)

                extracted = self.ocr_reader.extract_page_lines(page)
                lines = extracted["lines"]

                anchor_1 = self._detect_anchor_1_emblem(lines, h)
                detected_number = self._detect_anchor_2_doc_number(lines, w, h)
                detected_title = self._detect_anchor_3_title(lines, w, h)

                anchor_2 = bool(detected_number)
                anchor_3 = bool(detected_title)
                anchor_flags = [anchor_1, anchor_2, anchor_3]
                start_score = self._start_score(anchor_flags)

                # Use effective threshold based on OCR quality
                effective_threshold = self._get_effective_threshold(
                    extracted["avg_confidence"],
                    extracted["text_preview"],
                    extracted["source"]
                )

                # Check if this is a start page using integer comparison (avoids float rounding issues)
                anchor_count = sum(1 for x in anchor_flags if x)
                anchor_needed = int(effective_threshold * 3 + 0.5)  # Round: 0.67*3=2.01 → 2 needed
                is_start = anchor_count >= anchor_needed

                if idx == 0:
                    is_start = True

                if idx != 0 and is_start:
                    suggested_breaks.append(idx)

                pages_output.append(
                    {
                        "page_index": idx,
                        "is_start_page": is_start,
                        "start_score": round(float(start_score), 2),
                        "detected_title": detected_title,
                        "detected_number": detected_number,
                        "text_preview": extracted["text_preview"],
                        "source": extracted["source"],
                        "confidence": round(float(extracted["avg_confidence"]), 4),
                        "anchors": {
                            "anchor_1_emblem": anchor_1,
                            "anchor_2_doc_number": anchor_2,
                            "anchor_3_title": anchor_3,
                        },
                        "effective_threshold": round(effective_threshold, 2),
                    }
                )

            return {
                "file_path": str(path),
                "total_pages": len(doc),
                "suggested_breaks": sorted(set(suggested_breaks)),
                "pages": pages_output,
                "threshold": self.start_threshold,
            }
        finally:
            doc.close()

    def split_pdf(
        self,
        file_path: str,
        output_folder: str,
        break_points: List[int],
        names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        src = Path(file_path)
        if not src.exists():
            raise FileNotFoundError(f"PDF not found: {src}")

        out_dir = Path(output_folder)
        out_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(src))
        total_pages = len(doc)

        clean_breaks = sorted({int(p) for p in break_points if 0 <= int(p) < total_pages})
        if not clean_breaks or clean_breaks[0] != 0:
            clean_breaks.insert(0, 0)

        parts: List[Dict[str, Any]] = []

        try:
            for i, start in enumerate(clean_breaks):
                next_start = clean_breaks[i + 1] if i + 1 < len(clean_breaks) else total_pages
                if next_start <= start:
                    continue

                explicit_name = ""
                if names and i < len(names):
                    explicit_name = (names[i] or "").strip()
                file_name = explicit_name or f"part_{i + 1:03d}_pages_{start + 1}-{next_start}.pdf"
                if not file_name.lower().endswith(".pdf"):
                    file_name = f"{file_name}.pdf"

                out_path = out_dir / file_name
                sub_doc = fitz.open()
                sub_doc.insert_pdf(doc, from_page=start, to_page=next_start - 1)
                sub_doc.save(str(out_path))
                sub_doc.close()

                parts.append(
                    {
                        "index": i + 1,
                        "start_page": start,
                        "end_page": next_start - 1,
                        "file_name": file_name,
                        "file_path": str(out_path),
                    }
                )

            return {
                "total_pages": total_pages,
                "split_points": clean_breaks,
                "parts": parts,
            }
        finally:
            doc.close()


def analyze_pdf(file_path: str) -> Dict[str, Any]:
    """Convenience function required by integration code."""
    engine = SplitEngine()
    return engine.analyze_pdf(file_path)
