import React, { useCallback, useRef, useState, useEffect } from "react";
import axios from "axios";
import JSZip from "jszip";
import { saveAs } from "file-saver";
import { Eye, FileUp, Scissors, Loader2, Trash2, Plus } from "lucide-react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.js';

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

// ─── helpers ────────────────────────────────────────────────────────────────

const titleKeywords = ["HƯỚNG DẪN", "KẾ HOẠCH", "QUY ĐỊNH", "THÔNG BÁO", "NGHỊ QUYẾT", "CHỈ THỊ", "BÁO CÁO"];

const detectDocNumber = (text) => {
  const match = (text || "").match(/S[ốo]\s*[:]?\s*\d{1,4}\s*[-–]\s*[A-Z0-9]{1,12}\/[A-Z0-9.\-]{1,12}/i);
  return match ? match[0].replace(/\s+/g, " ").trim() : "";
};

const suggestName = (page) => {
  const preview = (page?.text_preview || "").trim();
  if (!preview) return "Van ban moi";
  const upper = preview.toUpperCase();
  const keyword = titleKeywords.find((k) => upper.includes(k));
  const docNo = detectDocNumber(preview);
  if (keyword && docNo) return `${keyword} ${docNo}`;
  if (keyword) return keyword;
  if (docNo) return `Van ban ${docNo}`;
  return preview.split(" ").slice(0, 7).join(" ");
};

const normalizeBreaks = (breaks, total) => {
  const valid = [...new Set((breaks || []).map(Number).filter((n) => Number.isInteger(n) && n >= 0 && n < total))].sort(
    (a, b) => a - b
  );
  if (!valid.length || valid[0] !== 0) valid.unshift(0);
  return valid;
};

const buildSegments = (breaks, pages, total) => {
  const norm = normalizeBreaks(breaks, total);
  return norm.map((start, idx) => {
    const end = Number.isInteger(norm[idx + 1]) ? norm[idx + 1] - 1 : total - 1;
    return {
      id: `seg-${start}`,
      startPage: start,
      endPage: end,
      name: suggestName(pages[start] || {}),
    };
  });
};

// ─── Inline PDF viewer panel ─────────────────────────────────────────────────

function PdfPanel({ fileUrl, startPage, endPage }) {
  const [page, setPage] = useState(startPage + 1);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setPage(startPage + 1);
    setReady(false);
  }, [startPage, endPage, fileUrl]);

  if (!fileUrl) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-slate-400">
        <Eye size={40} strokeWidth={1} />
        <p className="text-sm">Hover vào dòng để xem preview</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-3 py-2">
        <span className="text-xs font-medium text-slate-500">
          Phạm vi: trang {startPage + 1}–{endPage + 1}
        </span>
        <div className="flex items-center gap-2">
          <button
            disabled={page <= startPage + 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-30"
          >← Trước</button>
          <span className="text-xs font-medium text-slate-700">{page} / {endPage + 1}</span>
          <button
            disabled={page >= endPage + 1}
            onClick={() => setPage((p) => p + 1)}
            className="rounded px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-30"
          >Sau →</button>
        </div>
      </div>
      <div className="relative flex-1 overflow-auto bg-slate-100 flex justify-center p-2">
        {!ready && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">Đang tải...</div>
        )}
        <Document file={fileUrl} onLoadSuccess={() => setReady(true)} onLoadError={() => setReady(true)} loading={null}>
          <Page pageNumber={page} renderTextLayer={false} renderAnnotationLayer={false} width={340} />
        </Document>
      </div>
    </div>
  );
}

// ─── Main component ──────────────────────────────────────────────────────────

export default function DigitalizationGrid() {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [fileId, setFileId] = useState("");
  const [totalPages, setTotalPages] = useState(0);
  const [allPages, setAllPages] = useState([]);
  const [segments, setSegments] = useState([]);   // [{id, startPage, endPage, name}]
  const [hoveredSeg, setHoveredSeg] = useState(null);

  const [loadingStage, setLoadingStage] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [addBreakInput, setAddBreakInput] = useState("");

  const isBusy = Boolean(loadingStage);

  // ── upload & analyze ──────────────────────────────────────────────────────

  const uploadAndAnalyze = useCallback(async (file) => {
    setError("");
    setSuccess("");
    setSegments([]);
    setHoveredSeg(null);
    setSelectedFile(file);
    try {
      setLoadingStage("Đang tải file lên...");
      const fd = new FormData();
      fd.append("file", file);
      const { data: up } = await axios.post(`${API_BASE}/upload`, fd);
      const id = up.file_id;
      setFileId(id);
      setTotalPages(up.total_pages);

      setLoadingStage(`AI đang phân tích (${up.total_pages} trang)...`);
      const { data: an } = await axios.get(`${API_BASE}/analyze/${id}`);
      const pages = an.pages || [];
      const total = Number(an.total_pages || up.total_pages);
      setAllPages(pages);
      setTotalPages(total);

      const breaks = an.suggested_breaks || [0];
      setSegments(buildSegments(breaks, pages, total));
      setSuccess("Phân tích xong. Kiểm tra preview và chỉnh điểm tách nếu cần.");
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Lỗi khi xử lý file.");
    } finally {
      setLoadingStage("");
    }
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    if (isBusy) return;
    const f = e.dataTransfer?.files?.[0];
    if (f?.type === "application/pdf") uploadAndAnalyze(f);
  }, [isBusy, uploadAndAnalyze]);

  const onInput = useCallback((e) => {
    const f = e.target.files?.[0];
    if (f?.type === "application/pdf") uploadAndAnalyze(f);
  }, [uploadAndAnalyze]);

  // ── edit segments ─────────────────────────────────────────────────────────

  const recompute = useCallback((newBreaks) => {
    setSegments(buildSegments(newBreaks, allPages, totalPages));
  }, [allPages, totalPages]);

  const removeSegment = useCallback((seg) => {
    if (segments.length <= 1) return;
    recompute(segments.map((s) => s.startPage).filter((p) => p !== seg.startPage));
  }, [segments, recompute]);

  const addBreak = useCallback(() => {
    const p = parseInt(addBreakInput, 10) - 1;  // user enters 1-based
    if (isNaN(p) || p <= 0 || p >= totalPages) {
      setError(`Số trang phải từ 2 đến ${totalPages}.`);
      return;
    }
    setError("");
    recompute([...new Set([...segments.map((s) => s.startPage), p])]);
    setAddBreakInput("");
  }, [addBreakInput, segments, totalPages, recompute]);

  const updateName = useCallback((id, newName) => {
    setSegments((prev) => prev.map((s) => (s.id === id ? { ...s, name: newName } : s)));
  }, []);

  const moveBreak = useCallback((seg, delta) => {
    if (seg.startPage === 0) return;
    const newStart = seg.startPage + delta;
    if (newStart <= 0 || newStart >= totalPages) return;
    const others = segments.map((s) => s.startPage).filter((p) => p !== seg.startPage);
    if (others.includes(newStart)) return;
    recompute([...others, newStart]);
  }, [segments, totalPages, recompute]);

  // ── split & download ──────────────────────────────────────────────────────

  const handleSplit = useCallback(async () => {
    if (!fileId || segments.length === 0) return;
    setError("");
    setSuccess("");
    try {
      const documents = segments.map((s, idx) => ({
        order: idx + 1,
        name: s.name.trim() || `van-ban-${idx + 1}`,
        start_page: s.startPage,
        end_page: s.endPage,
      }));

      setLoadingStage("Đang tách file...");
      const { data } = await axios.post(`${API_BASE}/split`, {
        file_id: fileId,
        break_points: segments.map((s) => s.startPage),
        documents,
      });

      setLoadingStage("Đang nén và tải về...");
      if (data?.zip_url) {
        const blob = await axios.get(`${API_BASE}${data.zip_url}`, { responseType: "blob" });
        saveAs(blob.data, `${fileId}.zip`);
      } else {
        const files = data?.output_files || [];
        const zip = new JSZip();
        await Promise.all(files.map(async (name) => {
          const res = await axios.get(`${API_BASE}/download/${fileId}/${encodeURIComponent(name)}`, { responseType: "blob" });
          zip.file(name, res.data);
        }));
        saveAs(await zip.generateAsync({ type: "blob" }), `${fileId}.zip`);
      }
      setSuccess("Tách và tải về thành công!");
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Lỗi khi tách file.");
    } finally {
      setLoadingStage("");
    }
  }, [fileId, segments]);

  // ── render ────────────────────────────────────────────────────────────────

  const previewSeg = hoveredSeg || segments[0];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-blue-600 py-5 text-center text-white mb-6">
        <h1 className="text-2xl font-bold">📄 PDF Split AI</h1>
        <p className="text-sm text-blue-100 mt-1">Upload file PDF scan — AI tự động nhận diện tiêu đề và gợi ý điểm ngắt</p>
      </header>

      <div className="mx-auto max-w-7xl px-4 space-y-4">
        {/* Upload zone */}
        <div
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => !isBusy && fileInputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed py-8 text-center transition bg-white ${
            isBusy ? "border-slate-200" : "border-sky-300 hover:bg-sky-50"
          }`}
        >
          <input ref={fileInputRef} type="file" accept="application/pdf" className="hidden" onChange={onInput} />
          <FileUp className="mb-2 h-7 w-7 text-sky-500" />
          <p className="text-sm font-medium text-slate-700">
            {selectedFile ? selectedFile.name : "Kéo-thả hoặc bấm để chọn file PDF"}
          </p>
        </div>

        {loadingStage && (
          <div className="flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-800">
            <Loader2 className="h-4 w-4 animate-spin" /> {loadingStage}
          </div>
        )}
        {error && <div className="rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {success && <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-700">{success}</div>}

        {/* Main: segments + preview */}
        {segments.length > 0 && (
          <div className="flex gap-4 pb-8">
            {/* Left: segment table */}
            <div className="flex-1 min-w-0">
              <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden">
                {/* Table header bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
                  <div>
                    <h3 className="font-semibold text-slate-800">Danh sách văn bản AI đề xuất ({segments.length} file)</h3>
                    <p className="text-xs text-slate-500">Tổng {totalPages} trang · Hover để xem preview · Bấm tên để đổi</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number" min={2} max={totalPages}
                      value={addBreakInput}
                      onChange={(e) => setAddBreakInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addBreak()}
                      placeholder={`Thêm điểm tách (2–${totalPages})`}
                      className="w-52 rounded-md border border-slate-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-sky-400"
                    />
                    <button onClick={addBreak} className="inline-flex items-center gap-1 rounded-md bg-sky-500 px-3 py-1 text-xs text-white hover:bg-sky-600">
                      <Plus size={13} /> Thêm
                    </button>
                  </div>
                </div>

                {/* Column headers */}
                <div className="grid grid-cols-[36px_1fr_130px_130px_90px_44px] gap-0 border-b border-slate-100 bg-slate-50 px-3 py-2 text-xs font-semibold uppercase text-slate-500">
                  <span>#</span><span>Tên file gợi ý</span><span>Trang bắt đầu</span><span>Trang kết thúc</span><span>Số trang</span><span></span>
                </div>

                {/* Rows */}
                {segments.map((seg, idx) => (
                  <div
                    key={seg.id}
                    onMouseEnter={() => setHoveredSeg(seg)}
                    className={`grid grid-cols-[36px_1fr_130px_130px_90px_44px] items-center gap-0 border-b border-slate-50 px-3 py-2 text-sm transition-colors ${
                      hoveredSeg?.id === seg.id ? "bg-sky-50 border-sky-100" : "hover:bg-slate-50"
                    }`}
                  >
                    <span className="text-slate-400 font-medium">{idx + 1}</span>

                    <input
                      value={seg.name}
                      onChange={(e) => updateName(seg.id, e.target.value)}
                      className="mr-3 rounded border border-transparent bg-transparent px-1 py-0.5 text-slate-800 focus:border-sky-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-300 w-full"
                    />

                    <div className="flex items-center gap-1 text-slate-700">
                      {seg.startPage > 0 && (
                        <button onClick={() => moveBreak(seg, -1)} title="Lùi 1 trang" className="text-slate-400 hover:text-sky-600 text-xs">◀</button>
                      )}
                      <span>Trang {seg.startPage + 1}</span>
                      {seg.startPage > 0 && (
                        <button onClick={() => moveBreak(seg, +1)} title="Tiến 1 trang" className="text-slate-400 hover:text-sky-600 text-xs">▶</button>
                      )}
                    </div>

                    <span className="text-slate-700">Trang {seg.endPage + 1}</span>
                    <span className="text-xs text-slate-400">{seg.endPage - seg.startPage + 1} trang</span>

                    <button
                      onClick={() => removeSegment(seg)}
                      disabled={segments.length <= 1}
                      title="Xóa điểm tách (gộp vào đoạn trên)"
                      className="flex items-center justify-center rounded p-1 text-rose-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-20"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))}

                {/* Split button */}
                <div className="flex justify-end px-4 py-3 border-t border-slate-100">
                  <button
                    onClick={handleSplit}
                    disabled={isBusy || segments.length === 0}
                    className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scissors className="h-4 w-4" />}
                    Tách PDF và Tải về (.zip)
                  </button>
                </div>
              </div>
            </div>

            {/* Right: PDF preview */}
            <div className="w-[390px] shrink-0">
              <div className="sticky top-4 rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden" style={{ height: "calc(100vh - 140px)" }}>
                <div className="border-b border-slate-100 px-3 py-2 bg-slate-50">
                  <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
                    {previewSeg ? `📄 ${previewSeg.name}` : "PDF Preview"}
                  </p>
                </div>
                <div style={{ height: "calc(100% - 38px)" }}>
                  <PdfPanel
                    fileUrl={fileId ? `${API_BASE}/file/${fileId}` : null}
                    startPage={previewSeg?.startPage ?? 0}
                    endPage={previewSeg?.endPage ?? 0}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
