import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageEnhance

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from paddleocr import PaddleOCR
except Exception:  # pragma: no cover
    PaddleOCR = None

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def normalize_text(value: str) -> str:
    text = (value or "").strip().upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


def validate_pdf_file(file_path: str) -> None:
    """
    Validate PDF file before processing.
    Raises: ValueError or FileNotFoundError with descriptive message.
    """
    path = Path(file_path)
    
    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"Tệp PDF không tồn tại: {path}")
    
    # Check file extension
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Tệp phải là PDF, nhưng nhận được: {path.suffix}")
    
    # Check file size (minimum only to detect corruption)
    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb < 0.01:  # 10KB minimum
        raise ValueError("Tệp PDF quá nhỏ hoặc bị hỏng")
    
    # Try to open PDF to validate it
    try:
        doc = fitz.open(str(path))
        page_count = len(doc)
        
        if page_count == 0:
            doc.close()
            raise ValueError("Tệp PDF không có trang nào")
        
        # Check first page dimensions
        first_page = doc[0]
        width = float(first_page.rect.width)
        height = float(first_page.rect.height)
        
        # Validate page dimensions (reasonable bounds for documents)
        if width < 100 or height < 100 or width > 10000 or height > 10000:
            doc.close()
            raise ValueError(f"Kích thước trang bất thường: {width}x{height}px")
        
        doc.close()
        logger.info(f"PDF validation passed: {page_count} pages, size {file_size_mb:.2f}MB")
    
    except fitz.FileError as e:
        raise ValueError(f"Tệp PDF bị hỏng hoặc không hợp lệ: {str(e)}")
    except Exception as e:
        if isinstance(e, (ValueError, FileNotFoundError)):
            raise
        raise ValueError(f"Lỗi đọc PDF: {str(e)}")


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
        # Core types
        "HUONG DAN",                    # Guidance
        "KE HOACH",                     # Plan
        "QUY DINH",                     # Regulation
        "THONG BAO",                    # Announcement
        "NGHI QUYET",                   # Resolution
        "QUYET DINH",                   # Decision
        # Government documents
        "GIAY MOI HOI NGHI",            # Invitation letter
        "CHI THI",                      # Directive
        "PHUONG CHIEN",                 # Strategy
        "CHI TIEU",                     # Index/Criteria
        "LE HOP",                       # Regulation
        "BAO CAO",                      # Report
        "DU TOAN",                      # Budget
        "THANH TOAN",                   # Settlement
        "GIAO TIEP",                    # Liaison
        "HOI THAO",                     # Conference
        "DAI HOI",                      # Congress
        "CUP THI",                      # Contest
        "GIAO LUU",                     # Exchange
        "HOP TAC",                      # Cooperation
        "TRUONG THANH",                 # Permanent
        "THU TUC",                      # Procedure
        "BIEN BAN",                     # Minutes
        "GIAY CHUNG CHI",               # Certificate
        "HOP DONG",                     # Contract
        "THOA THUAN",                   # Agreement
    }

    EMBLEM_PHRASES = {
        "DANG CONG SAN VIET NAM",
        "CONG HOA XA HOI CHU NGHIA VIET NAM",
    }

    DOC_NUMBER_RE = re.compile(r"\bSO\s*:?\s*\d+\s*[-/]\s*[A-Z0-9][A-Z0-9./-]*", re.IGNORECASE)
    DOC_NUMBER_FALLBACK_RE = re.compile(r"\b\d{1,4}\s*[-/]\s*[A-Z0-9]{1,12}(?:\s*/\s*[A-Z0-9.-]{1,12})?", re.IGNORECASE)
    DOC_NUMBER_SPLIT_RE = re.compile(
        r"\bSO\s*:?(?:\s*HIEU)?\s*[A-Z0-9]{0,6}\s*\d{1,4}\s*[-/]\s*[A-Z0-9][A-Z0-9./-]*",
        re.IGNORECASE,
    )

    def __init__(self, ocr_reader: Optional[DocumentOCR] = None, start_threshold: float = 1.0) -> None:
        self.ocr_reader = ocr_reader or DocumentOCR(use_ocr_fallback=True, lang="vi")
        self.start_threshold = start_threshold
        self.page_structures: List[Dict[str, Any]] = []  # Store page structure for cross-page analysis

    def _analyze_emblem_properties(self, lines: List[Dict[str, Any]], page_height: float, page_width: float) -> Dict[str, Any]:
        """
        Analyze emblem characteristics to distinguish cover page from header.
        Returns: {is_cover: bool, emblem_size: str, position: str, confidence: float}
        """
        top_limit = page_height * 0.42
        emblems = []

        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if y1 > top_limit:
                continue

            text_norm = normalize_text(line["text"])
            if any(phrase in text_norm for phrase in self.EMBLEM_PHRASES):
                emblems.append({
                    "y": y0,
                    "x": x0,
                    "width": x1 - x0,
                    "height": y1 - y0,
                    "text_len": len(text_norm),
                })
            elif self._has_token_group(text_norm, ["DANG", "CONG SAN", "VIET NAM"], min_hit=2):
                emblems.append({
                    "y": y0,
                    "x": x0,
                    "width": x1 - x0,
                    "height": y1 - y0,
                    "text_len": len(text_norm),
                })

        if not emblems:
            return {"is_cover": False, "emblem_size": "none", "position": "none", "confidence": 0.0}

        # Analyze emblem properties
        emblem = emblems[0]
        is_centered = abs((emblem["x"] + emblem["width"]/2) - page_width/2) < page_width * 0.15
        is_large = emblem["height"] > page_height * 0.08
        is_top = emblem["y"] < page_height * 0.15

        # Cover page: centered + large + near top
        is_cover = is_centered and is_large
        
        emblem_size = "large" if is_large else "small"
        position = "centered" if is_centered else "left_aligned"
        if is_top:
            position = "top_" + position

        confidence = 0.8 if is_cover else 0.5

        return {
            "is_cover": is_cover,
            "emblem_size": emblem_size,
            "position": position,
            "confidence": confidence,
            "emblem_count": len(emblems),
        }

    def _analyze_page_image_features(self, page: fitz.Page) -> Dict[str, Any]:
        """
        Fallback image analysis when OCR fails.
        Detect if page has content (non-empty), structure (grid/text lines).
        """
        try:
            if cv2 is None:
                return {"has_content": True, "is_mostly_empty": False, "has_structure": True}

            mat = fitz.Matrix(1.0, 1.0)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

            # Check if page is mostly empty (white)
            white_pixels = np.sum(gray > 240)
            total_pixels = gray.shape[0] * gray.shape[1]
            emptiness_ratio = white_pixels / total_pixels

            is_mostly_empty = emptiness_ratio > 0.95

            # Detect text lines via edge detection
            edges = cv2.Canny(gray, 50, 150)
            has_structure = np.sum(edges) > (total_pixels * 0.01)  # > 1% edges

            return {
                "has_content": not is_mostly_empty,
                "is_mostly_empty": is_mostly_empty,
                "has_structure": has_structure,
                "emptiness_ratio": emptiness_ratio,
            }
        except Exception:
            return {"has_content": True, "is_mostly_empty": False, "has_structure": True}

    @staticmethod
    def _has_token_group(text_norm: str, token_group: List[str], min_hit: int) -> bool:
        hits = 0
        for token in token_group:
            if token in text_norm:
                hits += 1
        return hits >= min_hit

    def _detect_anchor_1_emblem(self, lines: List[Dict[str, Any]], page_height: float) -> Dict[str, Any]:
        """
        Detect emblem (Quốc hiệu/Đảng hiệu) in top 42% of page.
        Requires clear evidence of Vietnamese government emblem, not just random keywords.
        Returns: {detected: bool, confidence: float, reason: str}
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
                return {"detected": True, "confidence": 0.95, "reason": "exact_phrase"}

            # Fuzzy matching: require minimum evidence of emblem
            if self._has_token_group(text_norm, ["DANG", "CONG SAN", "VIET NAM"], min_hit=2):
                return {"detected": True, "confidence": 0.85, "reason": "partial_match_dang"}
            if self._has_token_group(text_norm, ["CONG HOA", "XA HOI", "CHU NGHIA", "VIET NAM"], min_hit=3):
                return {"detected": True, "confidence": 0.90, "reason": "partial_match_cong_hoa"}

        # Combine all top lines to handle multi-line emblems
        combined_top_text = " ".join(top_text_parts)
        
        if not combined_top_text.strip():
            return {"detected": False, "confidence": 0.0, "reason": "no_text_in_top_area"}

        # For degraded scans: accept if we have solid evidence
        if self._has_token_group(combined_top_text, ["DANG", "CONG SAN", "VIET NAM"], min_hit=2):
            return {"detected": True, "confidence": 0.80, "reason": "combined_match_dang"}
        if self._has_token_group(combined_top_text, ["CONG HOA", "XA HOI", "CHU NGHIA", "VIET NAM"], min_hit=3):
            return {"detected": True, "confidence": 0.85, "reason": "combined_match_cong_hoa"}

        # Lenient: if multiple emblem keywords are present in top section
        emblem_keywords = {"DANG", "CONG", "VIET NAM", "HOA", "XA HOI", "CHU NGHIA"}
        keyword_hits = sum(1 for kw in emblem_keywords if kw in combined_top_text)
        
        if keyword_hits >= 5:
            return {"detected": True, "confidence": 0.55, "reason": "weak_multi_keyword"}

        return {"detected": False, "confidence": 0.0, "reason": "no_emblem_keywords"}

    def _detect_anchor_2_doc_number(self, lines: List[Dict[str, Any]], page_width: float, page_height: float) -> Dict[str, Any]:
        """
        Detect document number (Số hiệu văn bản).
        Returns: {detected: bool, value: str, confidence: float, reason: str}
        Robust to poor OCR quality on low-resolution scans.
        """
        # Extend y_limit from 0.70 to 0.85 for poor-quality docs where number placement varies
        y_limit = page_height * 0.85
        x_limit = page_width * 0.68

        def _normalize_ocr_number_noise(text_norm: str) -> str:
            # OCR often confuses separators/symbols around document number.
            t = text_norm.replace("|", "/")
            t = t.replace("I", "1")
            t = re.sub(r"\s+", " ", t).strip()
            return t

        # Phase 1: Look for standard "Số XX-YY/ZZ" pattern (most reliable)
        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if y0 > y_limit or x0 > x_limit:
                continue

            text = line["text"]
            text_norm = normalize_text(text)
            
            text_norm = _normalize_ocr_number_noise(text_norm)
            match = self.DOC_NUMBER_RE.search(text_norm)
            if match:
                return {"detected": True, "value": text.strip()[:120], "confidence": 0.95, "reason": "standard_format"}

        # Phase 2: Look for "Số" + some digits/pattern
        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if y0 > y_limit or x0 > x_limit:
                continue

            text = line["text"]
            text_norm = normalize_text(text)

            text_norm = _normalize_ocr_number_noise(text_norm)

            has_so_marker = bool(re.search(r"\bSO\b", text_norm))
            has_ky_hieu_marker = ("KY HIEU" in text_norm) or ("KI HIEU" in text_norm)

            if not has_so_marker and not has_ky_hieu_marker:
                continue

            pattern = r"SO\s*:?\s*\d{1,4}\s*[-/]"
            if re.search(pattern, text_norm):
                return {"detected": True, "value": text.strip()[:120], "confidence": 0.85, "reason": "so_prefix"}

            # OCR-noisy but still likely a document number marker line.
            if has_so_marker and re.search(r"\d{1,4}", text_norm):
                return {"detected": True, "value": text.strip()[:120], "confidence": 0.75, "reason": "so_with_digits"}

            # User rule: if line contains "SO" marker, still count anchor 2
            # even when OCR misses the number/pattern.
            if has_so_marker:
                return {"detected": True, "value": text.strip()[:120], "confidence": 0.68, "reason": "so_marker_only"}

            # Special case: no explicit number but has "KY HIEU" marker.
            if has_ky_hieu_marker:
                return {"detected": True, "value": text.strip()[:120], "confidence": 0.65, "reason": "ky_hieu_marker"}

        # Phase 2b: Combine nearby top-left lines to recover split OCR like
        # "SO:" on one line and "03-TB/DU" on the next line.
        # Extend search area for poor-quality docs
        left_area_x_limit = page_width * 0.65
        top_area_y_limit = page_height * 0.55
        candidate_lines: List[Dict[str, Any]] = []
        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if x0 <= left_area_x_limit and y0 <= top_area_y_limit:
                candidate_lines.append(line)

        candidate_lines.sort(key=lambda ln: (ln["bbox"][1], ln["bbox"][0]))

        for i in range(len(candidate_lines)):
            merged = []
            raw_parts = []
            for j in range(i, min(i + 3, len(candidate_lines))):
                part_raw = (candidate_lines[j].get("text") or "").strip()
                if not part_raw:
                    continue
                raw_parts.append(part_raw)
                merged.append(_normalize_ocr_number_noise(normalize_text(part_raw)))

            if not merged:
                continue

            merged_text = " ".join(merged)
            if self.DOC_NUMBER_SPLIT_RE.search(merged_text):
                return {
                    "detected": True,
                    "value": " ".join(raw_parts)[:120],
                    "confidence": 0.82,
                    "reason": "split_lines_recovered",
                }

        # Phase 3: Look in top-left for abbreviated patterns
        left_area_x_limit = page_width * 0.50
        top_area_y_limit = page_height * 0.35

        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if x0 > left_area_x_limit or y0 > top_area_y_limit:
                continue

            text = line["text"]
            text_norm = normalize_text(text)
            text_norm = _normalize_ocr_number_noise(text_norm)

            pattern = r"^SO[\s:]?(?:[A-Z]{1,4}[-/][A-Z0-9]{1,8}|[A-Z0-9].*)"
            if re.match(pattern, text_norm):
                return {"detected": True, "value": text.strip()[:120], "confidence": 0.80, "reason": "abbreviated"}

        # Phase 3b: Full-page fallback for poor OCR - if we find "SO HIEU" or "KY HIEU" marker anywhere
        for line in lines:
            text = line["text"]
            text_norm = normalize_text(text)
            text_norm = _normalize_ocr_number_noise(text_norm)
            
            # Catch explicit marker lines even if they have no number
            if bool(re.search(r"\bSO\s+HIEU\b", text_norm)) or bool(re.search(r"\bKY\s+HIEU\b", text_norm)):
                return {"detected": True, "value": text.strip()[:120], "confidence": 0.72, "reason": "marker_line_fallback"}

        # Phase 4: Standalone numbers in top-left
        left_area_x_limit = page_width * 0.45
        top_area_y_limit = page_height * 0.30

        for line in lines:
            x0, y0, x1, y1 = line["bbox"]
            if x0 > left_area_x_limit or y0 > top_area_y_limit:
                continue

            text = line["text"]
            text_norm = normalize_text(text)
            text_norm = _normalize_ocr_number_noise(text_norm)

            strict_pattern = r"^\d{1,4}\s*[-/]\s*[A-Z0-9]{1,12}(?:\s*/\s*[A-Z0-9.-]{1,8})?$"
            
            if re.match(strict_pattern, text_norm):
                return {"detected": True, "value": text.strip()[:120], "confidence": 0.70, "reason": "standalone"}

        return {"detected": False, "value": "", "confidence": 0.0, "reason": "not_found"}

    def _detect_anchor_3_title(
        self,
        lines: List[Dict[str, Any]],
        page_width: float,
        page_height: float,
    ) -> Dict[str, Any]:
        """
        Detect document title (Tên loại văn bản).
        Returns: {detected: bool, value: str, confidence: float, reason: str}
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

            alpha_chars = [c for c in text if c.isalpha()]
            is_upper_like = bool(alpha_chars) and text == text.upper()
            word_count = len(text_norm.split())
            looks_standalone = word_count <= 10

            if is_upper_like or looks_standalone:
                conf = 0.90 if is_upper_like and is_centered else 0.85
                return {"detected": True, "value": text, "confidence": conf, "reason": "strict_centered"}

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
                if word_count <= 15:
                    return {"detected": True, "value": text, "confidence": 0.75, "reason": "lenient_centered"}

        # Phase 3: Partial keyword matching
        for line in lines:
            text = (line["text"] or "").strip()
            if not text or len(text) < 3:
                continue

            x0, y0, x1, y1 = line["bbox"]
            if y1 > top_limit:
                continue

            text_norm = normalize_text(text)
            
            for title in self.TITLE_TYPES:
                title_parts = title.split()
                if len(title_parts) > 1:
                    matches = sum(1 for part in title_parts if part in text_norm)
                    if matches >= 2:
                        line_center = (x0 + x1) / 2.0
                        is_vaguely_centered = abs(line_center - center_x) <= page_width * 0.45
                        word_count = len(text_norm.split())
                        
                        if is_vaguely_centered and word_count <= 20:
                            return {"detected": True, "value": text, "confidence": 0.65, "reason": "partial_match"}

        return {"detected": False, "value": "", "confidence": 0.0, "reason": "not_found"}

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

    def _calculate_weighted_anchor_score(self, anchors: List[bool], emblem_props: Dict[str, Any], page_idx: int) -> float:
        """
        Calculate weighted anchor score considering context:
        - Emblem: 0.4x if header (small), 1.0x if cover (large)
        - Title: 0.8x if on first page (header), 1.0x if isolated
        - Number: 1.0x always (strong signal)
        - Previous page pattern: reduce weight if same anchors repeated
        """
        anchor_1, anchor_2, anchor_3 = anchors
        all_three_present = anchor_1 and anchor_2 and anchor_3
        
        # Base weights
        emblem_weight = 1.0
        number_weight = 1.0
        title_weight = 1.0

        # Adjust emblem weight based on properties
        if emblem_props.get("is_cover"):
            emblem_weight = 1.0  # Cover emblem = full weight
        elif emblem_props.get("emblem_size") == "small":
            # If all 3 anchors present on non-early pages, small emblem is likely cover, not header
            if all_three_present and page_idx > 5:
                emblem_weight = 1.0  # Treat as cover emblem when all anchors present
            else:
                emblem_weight = 0.4  # Header emblem = less weight
        else:
            emblem_weight = 0.7  # Medium emblem

        # Adjust title weight based on page position
        if page_idx <= 1:  # First 2 pages: title might be header
            title_weight = 0.8
        else:
            title_weight = 1.0

        # Calculate weighted score
        weighted_score = 0.0
        if anchor_1:
            weighted_score += emblem_weight * (1.0 / 3.0)
        if anchor_2:
            weighted_score += number_weight * (1.0 / 3.0)
        if anchor_3:
            weighted_score += title_weight * (1.0 / 3.0)

        return weighted_score

    def _apply_cross_page_context(self, pages_output: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze cross-page patterns:
        - If emblem repeats on consecutive pages → reduce weight on page 2+
        - If all 3 anchors appear on first occurrence → strong signal
        - If emblem appears but no other signals → likely header, not start
        """
        if not pages_output:
            return pages_output

        # Track emblem continuity
        emblem_continuity = 0
        max_emblem_sequence = 0

        for idx, page in enumerate(pages_output):
            anchor_1 = page["anchors"]["anchor_1_emblem"]
            
            if anchor_1:
                emblem_continuity += 1
                max_emblem_sequence = max(max_emblem_sequence, emblem_continuity)
            else:
                emblem_continuity = 0

            # Heuristic: if we've seen emblem on many consecutive pages,
            # current emblem alone is NOT a start signal
            if emblem_continuity > 2 and idx > 1:
                # This is likely a header emblem, reduce weight
                current_score = page["start_score"]
                if page["anchors"]["anchor_1_emblem"] and not (page["anchors"]["anchor_2_doc_number"] or page["anchors"]["anchor_3_title"]):
                    # Emblem only → likely header
                    page["start_score"] = max(0.2, current_score * 0.3)
                    page["anchors"]["anchor_1_emblem"] = False  # Disable this anchor
                    page["is_start_page"] = False

        return pages_output

    def analyze_pdf(self, file_path: str) -> Dict[str, Any]:

        # Validate file first (raises ValueError or FileNotFoundError if invalid)
        validate_pdf_file(file_path)
        
        path = Path(file_path)
        doc = None
        pages_output: List[Dict[str, Any]] = []
        suggested_breaks: List[int] = [0]

        try:
            logger.info(f"Opening PDF: {path}")
            doc = fitz.open(str(path))
            
            if len(doc) == 0:
                raise ValueError("PDF has no pages")
            
            logger.info(f"Analyzing {len(doc)} pages with threshold={self.start_threshold}")
            
            for idx in range(len(doc)):
                try:
                    page = doc[idx]
                    w = float(page.rect.width)
                    h = float(page.rect.height)
                    
                    logger.debug(f"Page {idx}: {w}x{h}px")

                    extracted = self.ocr_reader.extract_page_lines(page)
                    lines = extracted["lines"]
                    logger.debug(f"Page {idx}: extracted {len(lines)} lines, source={extracted.get('source')}, conf={extracted.get('avg_confidence'):.2f}")

                    # Detect anchors (now returns dict with confidence)
                    anchor_1_data = self._detect_anchor_1_emblem(lines, h)
                    anchor_2_data = self._detect_anchor_2_doc_number(lines, w, h)
                    anchor_3_data = self._detect_anchor_3_title(lines, w, h)
                    
                    logger.debug(f"Page {idx}: anchor1={anchor_1_data['reason']} ({anchor_1_data['confidence']}), anchor2={anchor_2_data['reason']} ({anchor_2_data['confidence']}), anchor3={anchor_3_data['reason']} ({anchor_3_data['confidence']})")

                    # Extract detected flags and values
                    anchor_1 = anchor_1_data.get("detected", False)
                    anchor_2 = anchor_2_data.get("detected", False)
                    anchor_3 = anchor_3_data.get("detected", False)
                    
                    detected_number = anchor_2_data.get("value", "")
                    detected_title = anchor_3_data.get("value", "")
                    anchor_flags = [anchor_1, anchor_2, anchor_3]
                    start_score = self._start_score(anchor_flags)

                    # Analyze emblem properties (cover vs header)
                    emblem_props = self._analyze_emblem_properties(lines, h, w)

                    # If OCR confidence is very low, fallback to image analysis
                    image_features = self._analyze_page_image_features(page)
                    
                    # If page is completely empty, skip
                    if image_features.get("is_mostly_empty"):
                        anchor_flags = [False, False, False]
                        start_score = 0.0
                        emblem_props["confidence"] = 0.0
                        logger.debug(f"Page {idx}: marked as empty (emptiness_ratio={image_features.get('emptiness_ratio', 0):.2f})")

                    # Calculate weighted score based on context
                    weighted_score = self._calculate_weighted_anchor_score(anchor_flags, emblem_props, idx)

                    # Use effective threshold based on OCR quality
                    effective_threshold = self._get_effective_threshold(
                        extracted["avg_confidence"],
                        extracted["text_preview"],
                        extracted["source"]
                    )

                    # Check if this is a start page using integer comparison
                    anchor_count = sum(1 for x in anchor_flags if x)
                    anchor_needed = int(effective_threshold * 3 + 0.5)
                    is_start = anchor_count >= anchor_needed

                    if idx == 0:
                        is_start = True

                    if idx != 0 and is_start:
                        suggested_breaks.append(idx)
                        logger.debug(f"Page {idx}: marked as start_page (anchor_count={anchor_count} >= {anchor_needed})")

                    pages_output.append(
                        {
                            "page_index": idx,
                            "is_start_page": is_start,
                            "start_score": round(float(start_score), 2),
                            "weighted_score": round(float(weighted_score), 2),
                            "detected_title": detected_title,
                            "detected_number": detected_number,
                            "text_preview": extracted["text_preview"],
                            "source": extracted["source"],
                            "confidence": round(float(extracted["avg_confidence"]), 4),
                            "anchors": {
                                "anchor_1_emblem": {
                                    "detected": anchor_1,
                                    "confidence": round(anchor_1_data.get("confidence", 0.0), 2),
                                    "reason": anchor_1_data.get("reason", "unknown")
                                },
                                "anchor_2_doc_number": {
                                    "detected": anchor_2,
                                    "confidence": round(anchor_2_data.get("confidence", 0.0), 2),
                                    "reason": anchor_2_data.get("reason", "unknown")
                                },
                                "anchor_3_title": {
                                    "detected": anchor_3,
                                    "confidence": round(anchor_3_data.get("confidence", 0.0), 2),
                                    "reason": anchor_3_data.get("reason", "unknown")
                                },
                            },
                            "effective_threshold": round(effective_threshold, 2),
                            "emblem_type": emblem_props.get("emblem_size", "none"),
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing page {idx}: {str(e)}", exc_info=True)
                    # Return minimal data for this page on error
                    pages_output.append({
                        "page_index": idx,
                        "is_start_page": False,
                        "start_score": 0.0,
                        "weighted_score": 0.0,
                        "detected_title": "",
                        "detected_number": "",
                        "text_preview": "[Error processing page]",
                        "source": "error",
                        "confidence": 0.0,
                        "anchors": {
                            "anchor_1_emblem": {"detected": False, "confidence": 0.0, "reason": "error"},
                            "anchor_2_doc_number": {"detected": False, "confidence": 0.0, "reason": "error"},
                            "anchor_3_title": {"detected": False, "confidence": 0.0, "reason": "error"},
                        },
                        "effective_threshold": self.start_threshold,
                        "emblem_type": "none",
                    })

            # Apply cross-page context analysis
            pages_output = self._apply_cross_page_context(pages_output)
            logger.info(f"Applied cross-page context analysis")

            # Recalculate suggested breaks after cross-page analysis
            suggested_breaks = [0]
            for page in pages_output:
                if page["page_index"] > 0 and page["is_start_page"]:
                    suggested_breaks.append(page["page_index"])

            logger.info(f"Analysis complete: {len(pages_output)} pages, {len(suggested_breaks)} break points")
            
            return {
                "file_path": str(path),
                "total_pages": len(doc),
                "suggested_breaks": sorted(set(suggested_breaks)),
                "pages": pages_output,
                "threshold": self.start_threshold,
            }
        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Invalid input: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during PDF analysis: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to analyze PDF: {str(e)}")
        finally:
            if doc:
                try:
                    doc.close()
                    logger.debug("PDF document closed")
                except Exception as e:
                    logger.warning(f"Error closing PDF: {str(e)}")

    def split_pdf(
        self,
        file_path: str,
        output_folder: str,
        break_points: List[int],
        names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        # Validate file first
        validate_pdf_file(file_path)
        
        src = Path(file_path)
        out_dir = Path(output_folder)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {out_dir}")
        except Exception as e:
            logger.error(f"Cannot create output directory {out_dir}: {str(e)}")
            raise

        doc = None
        parts: List[Dict[str, Any]] = []

        try:
            logger.info(f"Opening PDF for splitting: {src}")
            doc = fitz.open(str(src))
            total_pages = len(doc)
            
            if total_pages == 0:
                raise ValueError("PDF has no pages")
            
            logger.info(f"PDF has {total_pages} pages, splitting at points: {break_points}")

            # Validate and clean break points
            try:
                clean_breaks = sorted({int(p) for p in break_points if 0 <= int(p) < total_pages})
            except (TypeError, ValueError) as e:
                logger.error(f"Invalid break_points: {str(e)}")
                raise ValueError(f"Break points must be valid page indices: {str(e)}")
            
            if not clean_breaks or clean_breaks[0] != 0:
                clean_breaks.insert(0, 0)
                logger.debug(f"Adjusted break points to include 0: {clean_breaks}")

            for i, start in enumerate(clean_breaks):
                try:
                    next_start = clean_breaks[i + 1] if i + 1 < len(clean_breaks) else total_pages
                    if next_start <= start:
                        logger.warning(f"Skipping invalid range: start={start}, next={next_start}")
                        continue

                    explicit_name = ""
                    if names and i < len(names):
                        explicit_name = (names[i] or "").strip()
                    
                    file_name = explicit_name or f"part_{i + 1:03d}_pages_{start + 1}-{next_start}.pdf"
                    if not file_name.lower().endswith(".pdf"):
                        file_name = f"{file_name}.pdf"

                    # Sanitize file name
                    file_name = file_name.replace("\\", "_").replace("/", "_").replace(":", "_")
                    
                    out_path = out_dir / file_name
                    logger.debug(f"Splitting pages {start+1}-{next_start}: {file_name}")
                    
                    sub_doc = fitz.open()
                    try:
                        sub_doc.insert_pdf(doc, from_page=start, to_page=next_start - 1)
                        sub_doc.save(str(out_path))
                        logger.debug(f"Saved: {out_path}")
                        
                        parts.append(
                            {
                                "index": i + 1,
                                "start_page": start,
                                "end_page": next_start - 1,
                                "file_name": file_name,
                                "file_path": str(out_path),
                            }
                        )
                    finally:
                        try:
                            sub_doc.close()
                        except Exception as e:
                            logger.warning(f"Error closing sub-document: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error splitting pages {start+1}-{next_start+1}: {str(e)}", exc_info=True)
                    raise

            logger.info(f"PDF splitting complete: {len(parts)} files created")
            
            return {
                "total_pages": total_pages,
                "split_points": clean_breaks,
                "parts": parts,
            }
        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Invalid input: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during PDF splitting: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to split PDF: {str(e)}")
        finally:
            if doc:
                try:
                    doc.close()
                    logger.debug("PDF document closed")
                except Exception as e:
                    logger.warning(f"Error closing PDF: {str(e)}")


def analyze_pdf(file_path: str) -> Dict[str, Any]:
    """Convenience function required by integration code."""
    engine = SplitEngine()
    return engine.analyze_pdf(file_path)
