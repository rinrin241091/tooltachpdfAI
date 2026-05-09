import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# PaddleOCR – lazy-load to avoid heavy startup time
_ocr = None

def get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _ocr


# ── directories ──────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="PDF Split AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── schemas ───────────────────────────────────────────────────────────────────
class PageInfo(BaseModel):
    page_number: int          # 0-based
    text_preview: str
    is_title: bool
    confidence: float


class AnalyzeResponse(BaseModel):
    file_id: str
    total_pages: int
    suggested_breaks: List[int]   # 0-based page indices where new docs start
    pages: List[PageInfo]


class SplitRequest(BaseModel):
    file_id: str
    break_points: List[int]       # 0-based page indices (must include 0)


class SplitResponse(BaseModel):
    file_id: str
    output_files: List[str]       # filenames of generated PDFs


# ── helpers ───────────────────────────────────────────────────────────────────
def _is_title_line(text: str) -> bool:
    """
    Heuristic: a line is treated as a document title if it is:
      • short (≤ 120 chars after stripping)
      • ALL-CAPS  or  starts with a Roman/Arabic section number
      • not purely numeric
    """
    stripped = text.strip()
    if not stripped or len(stripped) > 120:
        return False
    if stripped.isnumeric():
        return False

    import re
    # Numbered heading patterns: "1.", "I.", "CHƯƠNG I", "MỤC 2", etc.
    numbered = re.match(
        r"^(CHƯƠNG|MỤC|PHẦN|SECTION|ARTICLE|ĐIỀU|BÀN|PART)[\s\d]",
        stripped, re.IGNORECASE
    )
    if numbered:
        return True

    # Roman numeral prefix
    roman = re.match(r"^(M{0,4})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.", stripped)
    if roman and roman.group(0):
        return True

    # Digit prefix like "1.", "2.1.", "3.2.4."
    digit_prefix = re.match(r"^\d+(\.\d+)*\.", stripped)
    if digit_prefix:
        return True

    # All uppercase (at least 3 alpha chars)
    alpha_chars = [c for c in stripped if c.isalpha()]
    if len(alpha_chars) >= 3 and stripped == stripped.upper():
        return True

    return False


def _extract_page_text(pdf_path: Path, page_number: int) -> tuple[str, float]:
    """
    Lay text tu mot trang PDF.
    Uu tien text layer co san (PyMuPDF) de tiet kiem tai nguyen.
    Chi dung PaddleOCR khi trang khong co text layer va paddleocr da duoc cai.
    Returns (text, avg_confidence).
    """
    doc = fitz.open(str(pdf_path))
    page = doc[page_number]
    text_layer = page.get_text("text") or ""
    has_text_layer = len(text_layer.strip()) >= 20

    if has_text_layer:
        doc.close()
        clean = text_layer.strip().replace("\n", " ")
        return clean, 1.0

    # Trang khong co text layer → thu PaddleOCR neu co san
    try:
        import numpy as np
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        doc.close()

        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, 3
        )
        ocr = get_ocr()
        result = ocr.ocr(img_array, cls=True)

        lines = []
        confidences = []
        if result and result[0]:
            for line in result[0]:
                lines.append(line[1][0])
                confidences.append(float(line[1][1]))

        combined = " ".join(lines)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return combined, avg_conf

    except Exception:
        # PaddleOCR chua cai hoac loi → tra ve chuoi rong, khong crash
        doc.close()
        return "", 0.0


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.post("/upload", summary="Upload a PDF file")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_id = str(uuid.uuid4())
    dest = UPLOAD_DIR / f"{file_id}.pdf"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = fitz.open(str(dest))
    total_pages = len(doc)
    doc.close()

    return {"file_id": file_id, "filename": file.filename, "total_pages": total_pages}


@app.get("/analyze/{file_id}", response_model=AnalyzeResponse, summary="Analyze PDF pages with OCR")
async def analyze_pdf(file_id: str, max_pages: Optional[int] = None):
    pdf_path = UPLOAD_DIR / f"{file_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    doc.close()

    limit = min(total_pages, max_pages) if max_pages else total_pages

    pages_info: List[PageInfo] = []
    suggested_breaks: List[int] = [0]  # first page always starts a new doc

    for i in range(limit):
        text, conf = _extract_page_text(pdf_path, i)
        # Check first meaningful line of OCR result
        first_line = text.split("  ")[0] if text else ""
        is_title = _is_title_line(first_line)

        if is_title and i != 0:
            suggested_breaks.append(i)

        pages_info.append(
            PageInfo(
                page_number=i,
                text_preview=text[:200],
                is_title=is_title,
                confidence=round(conf, 4),
            )
        )

    return AnalyzeResponse(
        file_id=file_id,
        total_pages=total_pages,
        suggested_breaks=suggested_breaks,
        pages=pages_info,
    )


@app.post("/split", response_model=SplitResponse, summary="Split PDF into sub-files")
async def split_pdf(body: SplitRequest):
    pdf_path = UPLOAD_DIR / f"{body.file_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    breaks = sorted(set(body.break_points))
    if not breaks or breaks[0] != 0:
        breaks = [0] + breaks

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)

    out_dir = OUTPUT_DIR / body.file_id
    out_dir.mkdir(parents=True, exist_ok=True)

    output_files: List[str] = []

    for idx, start in enumerate(breaks):
        end = breaks[idx + 1] if idx + 1 < len(breaks) else total_pages
        out_name = f"part_{idx + 1:03d}_pages_{start + 1}-{end}.pdf"
        out_path = out_dir / out_name

        sub_doc = fitz.open()
        sub_doc.insert_pdf(doc, from_page=start, to_page=end - 1)
        sub_doc.save(str(out_path))
        sub_doc.close()

        output_files.append(out_name)

    doc.close()
    return SplitResponse(file_id=body.file_id, output_files=output_files)


@app.get("/file/{file_id}", summary="Get original uploaded PDF")
async def get_file(file_id: str):
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"{file_id}.pdf",
    )


@app.get("/download/{file_id}/{filename}", summary="Download a split PDF")
async def download_file(file_id: str, filename: str):
    file_path = OUTPUT_DIR / file_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found.")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
    )


@app.delete("/cleanup/{file_id}", summary="Remove uploaded and output files")
async def cleanup(file_id: str):
    upload_file = UPLOAD_DIR / f"{file_id}.pdf"
    out_dir = OUTPUT_DIR / file_id
    if upload_file.exists():
        upload_file.unlink()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    return {"detail": "Cleaned up successfully."}
