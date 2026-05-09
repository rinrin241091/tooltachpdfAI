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

from pdf_splitter import SplitEngine


def _build_engine_for_mode(mode: str) -> SplitEngine:
    """
    Build SplitEngine with threshold based on analysis mode:
    - "strict" or "3/3": Require all 3 anchors (start_threshold=1.0)
    - "flexible" or "2/3": Accept 2 out of 3 anchors (start_threshold=0.67)
    - "auto" or default: Automatic adjustment based on OCR quality
    """
    if mode in ("flexible", "2/3"):
        # Flexible mode: accept 2/3 anchors
        return SplitEngine(start_threshold=0.67)
    elif mode in ("strict", "3/3"):
        # Strict mode: require all 3 anchors
        return SplitEngine(start_threshold=1.0)
    else:
        # Auto mode (default): 1.0, but will auto-adjust in analyze_pdf if OCR is poor
        return SplitEngine(start_threshold=1.0)


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
class AnchorDetail(BaseModel):
    """Per-anchor detection result with confidence and reason."""
    detected: bool
    confidence: float  # 0.0 to 1.0
    reason: str        # e.g., "exact_phrase", "standard_format", "strict_centered"


class AnchorSignals(BaseModel):
    anchor_1_emblem: AnchorDetail
    anchor_2_doc_number: AnchorDetail
    anchor_3_title: AnchorDetail


class PageInfo(BaseModel):
    page_index: int           # 0-based
    is_start_page: bool
    start_score: float
    weighted_score: Optional[float] = None  # Context-aware weighted score
    detected_title: str
    detected_number: str
    anchors: AnchorSignals
    text_preview: str
    confidence: float
    effective_threshold: float  # Dynamic threshold used for this page
    emblem_type: Optional[str] = None  # "large", "small", or "none"
    source: Optional[str] = None  # "text_layer" or "ocr"


class AnalyzeResponse(BaseModel):
    file_id: str
    total_pages: int
    suggested_breaks: List[int]   # 0-based page indices where new docs start
    pages: List[PageInfo]


class SplitRequest(BaseModel):
    file_id: str
    break_points: List[int]       # 0-based page indices (must include 0)
    document_names: Optional[List[str]] = None


class SplitResponse(BaseModel):
    file_id: str
    output_files: List[str]       # filenames of generated PDFs


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.post("/upload", summary="Upload a PDF file")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Chỉ chấp nhận tệp PDF.")

        file_id = str(uuid.uuid4())
        dest = UPLOAD_DIR / f"{file_id}.pdf"
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        doc = fitz.open(str(dest))
        total_pages = len(doc)
        doc.close()
        
        if total_pages == 0:
            dest.unlink()
            raise HTTPException(status_code=400, detail="Tệp PDF không có trang nào.")

        return {"file_id": file_id, "filename": file.filename, "total_pages": total_pages}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tải lên: {str(e)}")


@app.get("/analyze/{file_id}", response_model=AnalyzeResponse, summary="Analyze PDF pages with OCR")
async def analyze_pdf(file_id: str, max_pages: Optional[int] = None, mode: str = "strict"):
    try:
        pdf_path = UPLOAD_DIR / f"{file_id}.pdf"
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp PDF.")

        analysis = _build_engine_for_mode(mode).analyze_pdf(str(pdf_path))
        total_pages = int(analysis.get("total_pages", 0))

        raw_pages = analysis.get("pages", [])
        if max_pages is not None:
            raw_pages = raw_pages[: max(0, int(max_pages))]

        pages_info: List[PageInfo] = []
        for p in raw_pages:
            anchors = p.get("anchors", {}) or {}
            
            # Extract per-anchor confidence data
            a1 = anchors.get("anchor_1_emblem", {})
            a2 = anchors.get("anchor_2_doc_number", {})
            a3 = anchors.get("anchor_3_title", {})
            
            # Handle both legacy bool format and new AnchorDetail format
            anchor_1_detail = a1 if isinstance(a1, dict) else {"detected": bool(a1), "confidence": 0.0, "reason": "legacy"}
            anchor_2_detail = a2 if isinstance(a2, dict) else {"detected": bool(a2), "confidence": 0.0, "reason": "legacy"}
            anchor_3_detail = a3 if isinstance(a3, dict) else {"detected": bool(a3), "confidence": 0.0, "reason": "legacy"}
            
            pages_info.append(
                PageInfo(
                    page_index=int(p.get("page_index", 0)),
                    is_start_page=bool(p.get("is_start_page", False)),
                    start_score=float(p.get("start_score", 0.0)),
                    weighted_score=float(p.get("weighted_score", 0.0)),
                    detected_title=p.get("detected_title", "") or "",
                    detected_number=p.get("detected_number", "") or "",
                    anchors=AnchorSignals(
                        anchor_1_emblem=AnchorDetail(
                            detected=anchor_1_detail.get("detected", False),
                            confidence=float(anchor_1_detail.get("confidence", 0.0)),
                            reason=anchor_1_detail.get("reason", "unknown")
                        ),
                        anchor_2_doc_number=AnchorDetail(
                            detected=anchor_2_detail.get("detected", False),
                            confidence=float(anchor_2_detail.get("confidence", 0.0)),
                            reason=anchor_2_detail.get("reason", "unknown")
                        ),
                        anchor_3_title=AnchorDetail(
                            detected=anchor_3_detail.get("detected", False),
                            confidence=float(anchor_3_detail.get("confidence", 0.0)),
                            reason=anchor_3_detail.get("reason", "unknown")
                        ),
                    ),
                    text_preview=(p.get("text_preview", "") or "")[:200],
                    confidence=float(p.get("confidence", 0.0)),
                    effective_threshold=float(p.get("effective_threshold", 1.0)),
                    emblem_type=p.get("emblem_type", "none"),
                    source=p.get("source", "text_layer"),
                )
            )

        suggested_breaks = sorted({int(x) for x in analysis.get("suggested_breaks", [0])})
        if not suggested_breaks or suggested_breaks[0] != 0:
            suggested_breaks.insert(0, 0)

        return AnalyzeResponse(
            file_id=file_id,
            total_pages=total_pages,
            suggested_breaks=suggested_breaks,
            pages=pages_info,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Tệp PDF không tồn tại: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Lỗi xác thực: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích PDF: {str(e)}")


@app.post("/split", response_model=SplitResponse, summary="Split PDF into sub-files")
async def split_pdf(body: SplitRequest):
    try:
        pdf_path = UPLOAD_DIR / f"{body.file_id}.pdf"
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp PDF.")

        breaks = sorted({int(p) for p in body.break_points})
        if not breaks or breaks[0] != 0:
            breaks.insert(0, 0)

        out_dir = OUTPUT_DIR / body.file_id
        out_dir.mkdir(parents=True, exist_ok=True)

        split_result = SplitEngine().split_pdf(
            file_path=str(pdf_path),
            output_folder=str(out_dir),
            break_points=breaks,
            names=body.document_names,
        )
        output_files = [part["file_name"] for part in split_result.get("parts", [])]
        return SplitResponse(file_id=body.file_id, output_files=output_files)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Lỗi xác thực: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi chia tách PDF: {str(e)}")


@app.get("/file/{file_id}", summary="Get original uploaded PDF")
async def get_file(file_id: str):
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp PDF.")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"{file_id}.pdf",
    )


@app.get("/download/{file_id}/{filename}", summary="Download a split PDF")
async def download_file(file_id: str, filename: str):
    file_path = OUTPUT_DIR / file_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp đầu ra.")
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
