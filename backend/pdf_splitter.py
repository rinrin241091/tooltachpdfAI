import re
import traceback
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
import numpy as np

try:
    from paddleocr import PaddleOCR
except Exception:  # pragma: no cover
    PaddleOCR = None


# Cac tu khoa chi tieu loai van ban (in hoa can giua)
TITLE_KEYWORDS = {
    "HUONG DAN",
    "KE HOACH",
    "QUY DINH",
    "THONG BAO",
    "NGHI QUYET",
    "CHI THI",
    "BAO CAO",
    "QUYET DINH",
    "LENH",
    "HOI NGHI",
}

# Quoc hieu va Ten Dang
EMBLEM_PHRASES = {
    "DANG CONG SAN VIET NAM",
    "CONG HOA XA HOI CHU NGHIA VIET NAM",
}

# Ten co quan ban hanh: BAN CHAP HANH TRUNG UONG, HUYENUY, SO..., TONG CUC, v.v.
ORGANIZATION_KEYWORDS = {
    "BAN CHAP HANH TRUNG UONG",
    "HUYENUY",
    "THANH UY",
    "BAN BI THU",
    "SO CONG AN",
    "UY BAN NHAN DAN",
    "CUC",
    "BO",
    "TONG CUC",
    "VIEN",
    "TRUONG",
}

# So, ky hieu van ban: "Số 03-HD/TW", "Số 90-KH/HU", "So: ...", v.v.
# Phuong an 1: Tim chuoi co dang "So/Numero + so - chu + / + chu"
DOC_NO_PATTERN = re.compile(
    r"\b(SO|NUMERO)\s*:?\s*(\d{1,4})\s*[-–]\s*([A-Z0-9]{1,12})\s*/\s*([A-Z0-9.\-]{1,12})",
    flags=re.IGNORECASE,
)

# Dia chi va thoi gian: "Ha Noi, ngay 20 thang 3 nam 2020"
LOCATION_TIME_PATTERN = re.compile(
    r"(Ha[oi]\s*(Noi|NOI)|THANH PHO|TINH)\s*,\s*(NGAY|ngay)\s*\d{1,2}\s*(THANG|thang)\s*\d{1,2}",
    flags=re.IGNORECASE,
)

_ocr_instance: Optional[Any] = None


def _get_ocr() -> Any:
    global _ocr_instance
    if PaddleOCR is None:
        raise RuntimeError("paddleocr is not installed or failed to import.")
    if _ocr_instance is None:
        _ocr_instance = PaddleOCR(use_angle_cls=True, lang="vi", show_log=False)
    return _ocr_instance


def _normalize_text(text: str) -> str:
    text = (text or "").strip().upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


def _is_uppercase_title_like(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    alpha_chars = [c for c in raw if c.isalpha()]
    if len(alpha_chars) < 4:
        return False
    return raw == raw.upper()


def _extract_lines_from_text_layer(page: fitz.Page) -> List[Dict[str, Any]]:
    lines: List[Dict[str, Any]] = []
    text_dict = page.get_text("dict")

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(span.get("text", "") for span in spans).strip()
            if not text:
                continue
            x0, y0, x1, y1 = line.get("bbox", (0.0, 0.0, 0.0, 0.0))
            conf = 1.0
            lines.append(
                {
                    "text": text,
                    "bbox": (float(x0), float(y0), float(x1), float(y1)),
                    "conf": conf,
                    "source": "text_layer",
                }
            )
    return lines


def _extract_lines_from_ocr(page: fitz.Page, zoom: float = 2.0) -> List[Dict[str, Any]]:
    ocr = _get_ocr()
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    result = ocr.ocr(img, cls=True)

    lines: List[Dict[str, Any]] = []
    if not result or not result[0]:
        return lines

    scale_x = page.rect.width / pix.width
    scale_y = page.rect.height / pix.height

    for item in result[0]:
        box, payload = item[0], item[1]
        text = (payload[0] or "").strip()
        conf = float(payload[1]) if payload and len(payload) > 1 else 0.0
        if not text:
            continue

        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)

        lines.append(
            {
                "text": text,
                "bbox": (x0 * scale_x, y0 * scale_y, x1 * scale_x, y1 * scale_y),
                "conf": conf,
                "source": "ocr",
            }
        )

    return lines


def _extract_page_lines(page: fitz.Page) -> Dict[str, Any]:
    text_layer_raw = page.get_text("text") or ""
    has_text_layer = len(text_layer_raw.strip()) >= 20

    if has_text_layer:
        lines = _extract_lines_from_text_layer(page)
        if lines:
            return {
                "lines": lines,
                "source": "text_layer",
                "text_preview": text_layer_raw.strip().replace("\n", " ")[:240],
            }

    lines = _extract_lines_from_ocr(page)
    preview = " ".join(line["text"] for line in lines)[:240] if lines else ""
    return {
        "lines": lines,
        "source": "ocr",
        "text_preview": preview,
    }


def _detect_title_signal(lines: List[Dict[str, Any]], page_width: float, page_height: float) -> bool:
    """Phat hien ten loai van ban in hoa can giua o nua tren trang."""
    top_half_limit = page_height * 0.55
    center_x = page_width / 2.0

    for line in lines:
        text = line["text"]
        norm_text = _normalize_text(text)
        if not norm_text or len(norm_text) < 3:
            continue

        x0, y0, x1, y1 = line["bbox"]
        if y1 > top_half_limit:
            continue

        line_center = (x0 + x1) / 2.0
        is_centered = abs(line_center - center_x) <= page_width * 0.20
        if not is_centered:
            continue

        has_keyword = any(keyword in norm_text for keyword in TITLE_KEYWORDS)
        if not has_keyword:
            continue

        if _is_uppercase_title_like(text):
            return True

    return False


def _detect_emblem_signal(lines: List[Dict[str, Any]], page_width: float, page_height: float) -> bool:
    """Phat hien quoc hieu va ten Dang o top."""
    top_limit = page_height * 0.35
    center_x = page_width / 2.0

    for line in lines:
        norm_text = _normalize_text(line["text"])
        if not norm_text:
            continue

        x0, y0, x1, y1 = line["bbox"]
        if y1 > top_limit:
            continue

        line_center = (x0 + x1) / 2.0
        in_top_right = x0 >= page_width * 0.48
        in_top_center = abs(line_center - center_x) <= page_width * 0.22

        if not (in_top_right or in_top_center):
            continue

        if any(phrase in norm_text for phrase in EMBLEM_PHRASES):
            return True

    return False


def _detect_organization_signal(lines: List[Dict[str, Any]], page_width: float, page_height: float) -> bool:
    """Phat hien ten co quan ban hanh."""
    top_limit = page_height * 0.45
    
    for line in lines:
        norm_text = _normalize_text(line["text"])
        if not norm_text:
            continue

        x0, y0, x1, y1 = line["bbox"]
        if y1 > top_limit:
            continue

        if any(org in norm_text for org in ORGANIZATION_KEYWORDS):
            return True

    return False


def _detect_doc_number_signal(lines: List[Dict[str, Any]], page_width: float, page_height: float) -> bool:
    """Phat hien so, ky hieu van ban."""
    vertical_limit = page_height * 0.60

    for line in lines:
        text = line["text"]
        norm_text = _normalize_text(text)

        x0, y0, x1, y1 = line["bbox"]
        if y0 > vertical_limit:
            continue

        if x0 > page_width * 0.55:
            continue

        if DOC_NO_PATTERN.search(norm_text):
            return True

    return False


def _detect_location_time_signal(lines: List[Dict[str, Any]], page_width: float, page_height: float) -> bool:
    """Phat hien dia chi va thoi gian ban hanh."""
    vertical_limit = page_height * 0.70
    
    for line in lines:
        text = line["text"]
        norm_text = _normalize_text(text)

        x0, y0, x1, y1 = line["bbox"]
        if y0 > vertical_limit:
            continue

        if LOCATION_TIME_PATTERN.search(norm_text):
            return True

    return False


def detect_split_points(pdf_path: str) -> Dict[str, Any]:
    """
    Duyet tung trang PDF va tim diem bat dau van ban moi.
    Trigger: mot trang duoc xem la start_page neu co it nhat 2/4 dau hieu:
      1) Tieu de IN HOA, can giua, o nua tren (HUONG DAN, KE HOACH, ...)
      2) Quoc hieu / ten Dang o top (CONG HOA..., DANG CONG SAN...)
      3) So hieu van ban (03-HD/TW, 90-KH/HU, ...)
      4) Dia chi + thoi gian ban hanh (Ha Noi, ngay 20 thang 3 nam 2020)
    
    Them: Phat hien ten co quan ban hanh (BAN CHAP HANH TRUNG UONG, HUYENUY, ...)

    Returns (JSON-friendly dict):
    {
      "ok": bool,
      "pdf_path": str,
      "total_pages": int,
      "split_points": [int, ...],
      "pages": [...],
      "error": str | None
    }
    """
    path = Path(pdf_path)
    result: Dict[str, Any] = {
        "ok": False,
        "pdf_path": str(path),
        "total_pages": 0,
        "split_points": [],
        "pages": [],
        "error": None,
    }

    try:
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        doc = fitz.open(str(path))
        result["total_pages"] = len(doc)

        split_points: List[int] = [0]

        for idx in range(len(doc)):
            page = doc[idx]
            extracted = _extract_page_lines(page)
            lines = extracted["lines"]

            w = float(page.rect.width)
            h = float(page.rect.height)

            title_signal = _detect_title_signal(lines, w, h)
            emblem_signal = _detect_emblem_signal(lines, w, h)
            org_signal = _detect_organization_signal(lines, w, h)
            doc_no_signal = _detect_doc_number_signal(lines, w, h)
            location_time_signal = _detect_location_time_signal(lines, w, h)

            # Tong cong 5 dau hieu, yeu cau it nhat 2 dau hieu
            signal_count = (
                int(title_signal) 
                + int(emblem_signal) 
                + int(org_signal)
                + int(doc_no_signal) 
                + int(location_time_signal)
            )
            is_start_page = signal_count >= 2

            if idx != 0 and is_start_page:
                split_points.append(idx)

            result["pages"].append(
                {
                    "page_index": idx,
                    "source": extracted["source"],
                    "text_preview": extracted["text_preview"],
                    "signals": {
                        "title": title_signal,
                        "emblem": emblem_signal,
                        "organization": org_signal,
                        "doc_number": doc_no_signal,
                        "location_time": location_time_signal,
                        "matched_count": signal_count,
                    },
                    "is_start_page": is_start_page,
                }
            )

        doc.close()

        result["split_points"] = sorted(set(split_points))
        result["ok"] = True
        return result

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc(limit=3)
        return result


def split_pdf(input_path: str, output_folder: str, split_points: List[int]) -> Dict[str, Any]:
    """
    Cat PDF theo cac diem bat dau van ban.

    Returns (JSON-friendly dict):
    {
      "ok": bool,
      "input_path": str,
      "output_folder": str,
      "total_pages": int,
      "split_points": [int, ...],
      "parts": [{"index": int, "start_page": int, "end_page": int, "file_name": str, "file_path": str}],
      "error": str | None
    }
    """
    src = Path(input_path)
    out_dir = Path(output_folder)

    result: Dict[str, Any] = {
        "ok": False,
        "input_path": str(src),
        "output_folder": str(out_dir),
        "total_pages": 0,
        "split_points": [],
        "parts": [],
        "error": None,
    }

    try:
        if not src.exists():
            raise FileNotFoundError(f"PDF not found: {src}")

        out_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(src))
        total_pages = len(doc)
        result["total_pages"] = total_pages

        clean_points = sorted({int(p) for p in split_points if 0 <= int(p) < total_pages})
        if not clean_points or clean_points[0] != 0:
            clean_points = [0] + clean_points

        parts: List[Dict[str, Any]] = []

        for i, start in enumerate(clean_points):
            end = clean_points[i + 1] if i + 1 < len(clean_points) else total_pages
            if end <= start:
                continue

            out_name = f"part_{i + 1:03d}_pages_{start + 1}-{end}.pdf"
            out_path = out_dir / out_name

            chunk = fitz.open()
            chunk.insert_pdf(doc, from_page=start, to_page=end - 1)
            chunk.save(str(out_path))
            chunk.close()

            parts.append(
                {
                    "index": i + 1,
                    "start_page": start,
                    "end_page": end - 1,
                    "file_name": out_name,
                    "file_path": str(out_path),
                }
            )

        doc.close()

        result["split_points"] = clean_points
        result["parts"] = parts
        result["ok"] = True
        return result

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc(limit=3)
        return result
