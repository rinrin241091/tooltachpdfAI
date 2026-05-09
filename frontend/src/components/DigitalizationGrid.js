import React, { useCallback, useMemo, useRef, useState } from "react";
import axios from "axios";
import JSZip from "jszip";
import { saveAs } from "file-saver";
import { Download, FileUp, Loader2, Scissors } from "lucide-react";
import { Document, Page, pdfjs } from "react-pdf";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.js";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

function PdfPreviewCard({ fileId, pageIndex }) {
  if (!fileId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-400">
        Chưa có file để xem trước.
      </div>
    );
  }

  const pageNumber = (pageIndex ?? 0) + 1;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-100 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600">
        Xem trước trang {pageNumber}
      </div>
      <div className="flex-1 overflow-auto bg-slate-100 p-2">
        <div className="mx-auto w-fit">
          <Document file={`${API_BASE}/file/${fileId}`}>
            <Page pageNumber={pageNumber} width={360} renderAnnotationLayer={false} />
          </Document>
        </div>
      </div>
    </div>
  );
}

function makeSafeFileName(pageRow, order) {
  const title = (pageRow?.detected_title || "").trim();
  const number = (pageRow?.detected_number || "").trim();
  const raw = `${title} ${number}`.trim() || `van-ban-${order}`;
  return raw.replace(/[\\/:*?"<>|]+/g, "-").replace(/\s+/g, " ").trim();
}

function asAnchorDetail(anchorLike) {
  if (anchorLike && typeof anchorLike === "object") {
    return {
      detected: Boolean(anchorLike.detected),
      confidence: Number(anchorLike.confidence || 0),
      reason: String(anchorLike.reason || "unknown"),
    };
  }

  return {
    detected: Boolean(anchorLike),
    confidence: 0,
    reason: "legacy",
  };
}

function AnchorBadge({ label, anchorData }) {
  const detail = asAnchorDetail(anchorData);
  const title = `${detail.reason} (${Math.round(detail.confidence * 100)}%)`;

  return (
    <span
      title={title}
      className={`rounded-full px-2 py-0.5 text-[11px] font-semibold transition ${
        detail.detected ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
      }`}
    >
      {label}: {detail.detected ? "Có" : "Không"}
      {detail.confidence > 0 ? ` (${Math.round(detail.confidence * 100)}%)` : ""}
    </span>
  );
}

function StatsDashboard({ rows, totalPages }) {
  if (!rows.length) return null;

  const toVietnameseEmblemType = (type) => {
    if (type === "small") return "quốc huy nhỏ";
    if (type === "large") return "quốc huy lớn";
    if (type === "none") return "không có";
    return type;
  };

  const startPages = rows.filter((r) => r.is_start_page).length;
  const avgStartScore = rows.reduce((s, r) => s + Number(r.start_score || 0), 0) / rows.length;
  const avgWeightedScore = rows.reduce((s, r) => s + Number(r.weighted_score || 0), 0) / rows.length;
  const successRate = totalPages > 0 ? (startPages / totalPages) * 100 : 0;

  const emblemDist = rows.reduce((acc, r) => {
    const key = r.emblem_type || "none";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
        <p className="text-xs text-emerald-700">Tỷ lệ đề xuất</p>
        <p className="mt-1 text-xl font-bold text-emerald-800">{successRate.toFixed(1)}%</p>
        <p className="text-xs text-emerald-700">{startPages}/{totalPages} trang</p>
      </div>

      <div className="rounded-lg border border-sky-200 bg-sky-50 p-3">
        <p className="text-xs text-sky-700">Điểm trung bình</p>
        <p className="mt-1 text-xl font-bold text-sky-800">{avgStartScore.toFixed(2)}</p>
        <p className="text-xs text-sky-700">Điểm có trọng số: {avgWeightedScore.toFixed(2)}</p>
      </div>

      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-3 md:col-span-2 xl:col-span-2">
        <p className="text-xs text-indigo-700">Phân bố quốc huy</p>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {Object.entries(emblemDist).map(([k, v]) => (
            <span key={k} className="rounded-full bg-white px-2 py-1 text-indigo-700 ring-1 ring-indigo-200">
              {toVietnameseEmblemType(k)}: {v}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function DigitalizationGrid() {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [fileId, setFileId] = useState("");
  const [totalPages, setTotalPages] = useState(0);
  const [rows, setRows] = useState([]);
  const [hoveredPageIndex, setHoveredPageIndex] = useState(0);
  const [analysisMode, setAnalysisMode] = useState("strict");
  const [effectiveThreshold, setEffectiveThreshold] = useState(1.0);

  const [loadingStage, setLoadingStage] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const isBusy = Boolean(loadingStage);

  const startPages = useMemo(() => {
    const starts = rows
      .filter((r) => r.is_start_page)
      .map((r) => Number(r.page_index))
      .filter((n) => Number.isInteger(n) && n >= 0)
      .sort((a, b) => a - b);

    if (!starts.length || starts[0] !== 0) {
      starts.unshift(0);
    }
    return [...new Set(starts)];
  }, [rows]);

  const rowByPageIndex = useMemo(() => {
    const map = new Map();
    rows.forEach((r) => map.set(r.page_index, r));
    return map;
  }, [rows]);

  const applyAnalyzeResult = useCallback((analyzed, fallbackTotal = 0) => {
    const incoming = (analyzed.pages || []).map((p) => ({
      page_index: Number(p.page_index),
      is_start_page: Boolean(p.is_start_page),
      start_score: Number(p.start_score || 0),
      weighted_score: Number(p.weighted_score || 0),
      detected_title: p.detected_title || "",
      detected_number: p.detected_number || "",
      anchor_1_emblem: asAnchorDetail(p.anchors?.anchor_1_emblem),
      anchor_2_doc_number: asAnchorDetail(p.anchors?.anchor_2_doc_number),
      anchor_3_title: asAnchorDetail(p.anchors?.anchor_3_title),
      text_preview: p.text_preview || "",
      confidence: Number(p.confidence || 0),
      effective_threshold: Number(p.effective_threshold || 1.0),
      emblem_type: p.emblem_type || "none",
      source: p.source || "text_layer",
    }));

    const thresh = incoming.length > 0 ? incoming[0].effective_threshold : 1.0;
    setEffectiveThreshold(thresh);

    setRows(incoming);
    setHoveredPageIndex(0);
    setTotalPages(Number(analyzed.total_pages || fallbackTotal || incoming.length));
  }, []);

  const uploadAndAnalyze = useCallback(
    async (file) => {
      setError("");
      setSuccess("");
      setRows([]);
      setSelectedFile(file);

      try {
        setLoadingStage("Đang tải lên PDF...");
        const fd = new FormData();
        fd.append("file", file);
        const { data: up } = await axios.post(`${API_BASE}/upload`, fd);

        const uploadedFileId = up.file_id;
        setFileId(uploadedFileId);
        setTotalPages(Number(up.total_pages || 0));

        setLoadingStage("AI đang phân tích tài liệu...");
        const { data: analyzed } = await axios.get(`${API_BASE}/analyze/${uploadedFileId}`, {
          params: { mode: analysisMode },
        });

        applyAnalyzeResult(analyzed, Number(up.total_pages || 0));

        let msg = "";
        if (analysisMode === "flexible") {
          msg = "Chế độ linh hoạt (2/3): AI đề xuất nếu có ít nhất 2 mỏ neo.";
        } else if (effectiveThreshold < 1.0) {
          msg = "AI tự giảm ngưỡng do OCR yếu. Bạn có thể chỉnh thủ công từng trang.";
        } else {
          msg = "Chế độ chặt chẽ (3/3): Chỉ đề xuất khi đủ 3 mỏ neo.";
        }
        setSuccess(msg);
      } catch (e) {
        setError(e?.response?.data?.detail || e.message || "Không thể tải lên hoặc phân tích file.");
      } finally {
        setLoadingStage("");
      }
    },
    [analysisMode, applyAnalyzeResult, effectiveThreshold]
  );

  const reAnalyzeCurrent = useCallback(async () => {
    if (!fileId) return;

    setError("");
    setSuccess("");
    try {
      setLoadingStage("Đang phân tích lại theo chế độ đã chọn...");
      const { data: analyzed } = await axios.get(`${API_BASE}/analyze/${fileId}`, {
        params: { mode: analysisMode },
      });
      applyAnalyzeResult(analyzed, totalPages);

      setSuccess(
        analysisMode === "flexible"
          ? "Phân tích lại với chế độ linh hoạt (2/3)."
          : "Phân tích lại với chế độ chặt chẽ (3/3)."
      );
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Không thể phân tích lại.");
    } finally {
      setLoadingStage("");
    }
  }, [analysisMode, applyAnalyzeResult, fileId, totalPages]);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      if (isBusy) return;
      const file = event.dataTransfer?.files?.[0];
      if (file?.type === "application/pdf") {
        uploadAndAnalyze(file);
      }
    },
    [isBusy, uploadAndAnalyze]
  );

  const onInput = useCallback(
    (event) => {
      const file = event.target.files?.[0];
      if (file?.type === "application/pdf") {
        uploadAndAnalyze(file);
      }
    },
    [uploadAndAnalyze]
  );

  const toggleStartPage = useCallback((pageIndex) => {
    setRows((prev) =>
      prev.map((row) => {
        if (row.page_index === pageIndex) {
          if (row.page_index === 0) {
            return { ...row, is_start_page: true };
          }
          return { ...row, is_start_page: !row.is_start_page };
        }
        return row;
      })
    );
  }, []);

  const exportJson = useCallback(() => {
    if (!rows.length) {
      setError("Chưa có dữ liệu để xuất.");
      return;
    }

    const payload = {
      file_id: fileId,
      total_pages: totalPages,
      analysis_mode: analysisMode,
      effective_threshold: effectiveThreshold,
      exported_at: new Date().toISOString(),
      rows,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    saveAs(blob, `analysis-${fileId || "result"}.json`);
  }, [analysisMode, effectiveThreshold, fileId, rows, totalPages]);

  const exportCsv = useCallback(() => {
    if (!rows.length) {
      setError("Chưa có dữ liệu để xuất.");
      return;
    }

    const header = [
      "page_index",
      "is_start_page",
      "start_score",
      "weighted_score",
      "detected_title",
      "detected_number",
      "anchor_1_detected",
      "anchor_1_confidence",
      "anchor_2_detected",
      "anchor_2_confidence",
      "anchor_3_detected",
      "anchor_3_confidence",
      "emblem_type",
      "source",
    ];

    const lines = rows.map((r) => {
      const cols = [
        r.page_index,
        r.is_start_page,
        r.start_score,
        r.weighted_score,
        (r.detected_title || "").replaceAll('"', '""'),
        (r.detected_number || "").replaceAll('"', '""'),
        r.anchor_1_emblem?.detected,
        r.anchor_1_emblem?.confidence,
        r.anchor_2_doc_number?.detected,
        r.anchor_2_doc_number?.confidence,
        r.anchor_3_title?.detected,
        r.anchor_3_title?.confidence,
        r.emblem_type,
        r.source,
      ];

      return cols
        .map((c) => {
          if (typeof c === "string") return `"${c}"`;
          return String(c ?? "");
        })
        .join(",");
    });

    const content = [header.join(","), ...lines].join("\n");
    const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
    saveAs(blob, `analysis-${fileId || "result"}.csv`);
  }, [fileId, rows]);

  const handleSplit = useCallback(async () => {
    if (!fileId || !rows.length) {
      setError("Chưa có dữ liệu để tách.");
      return;
    }

    setError("");
    setSuccess("");

    try {
      const names = startPages.map((pageIndex, idx) => makeSafeFileName(rowByPageIndex.get(pageIndex), idx + 1));

      setLoadingStage("Đang gửi danh sách trang bắt đầu lên backend...");
      const { data } = await axios.post(`${API_BASE}/split`, {
        file_id: fileId,
        break_points: startPages,
        document_names: names,
      });

      const files = data?.output_files || [];
      if (!files.length) {
        throw new Error("Không nhận được file kết quả từ backend.");
      }

      setLoadingStage("Đang đóng gói file .zip...");
      const zip = new JSZip();

      await Promise.all(
        files.map(async (name) => {
          const res = await axios.get(`${API_BASE}/download/${fileId}/${encodeURIComponent(name)}`, {
            responseType: "blob",
          });
          zip.file(name, res.data);
        })
      );

      const blob = await zip.generateAsync({ type: "blob" });
      saveAs(blob, `${fileId}.zip`);
      setSuccess("Đã tách file và tải zip thành công.");
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Không thể tách file.");
    } finally {
      setLoadingStage("");
    }
  }, [fileId, rowByPageIndex, rows.length, startPages]);

  const suggestedCount = startPages.length;

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-gradient-to-r from-sky-700 to-blue-600 px-6 py-6 text-white shadow-lg">
        <div className="mx-auto max-w-7xl">
          <h1 className="text-2xl font-bold tracking-tight">Bảng điều khiển tách PDF</h1>
          <p className="mt-1 text-sm text-sky-100">
            Hiển thị danh sách từng trang và đánh dấu đề xuất tách theo 2/3 hoặc 3/3 mỏ neo tùy chọn.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-6">
        <div className="mb-4 flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3">
          <span className="text-sm font-semibold text-slate-700">Quy tắc nhận diện:</span>
          <select
            value={analysisMode}
            onChange={(e) => setAnalysisMode(e.target.value)}
            className="rounded-md border border-slate-300 px-2 py-1 text-sm text-slate-700"
            disabled={isBusy}
          >
            <option value="strict">Bắt buộc 3/3 mỏ neo (chặt chẽ)</option>
            <option value="flexible">Bắt buộc 2/3 mỏ neo (linh hoạt)</option>
          </select>
          <button
            type="button"
            onClick={reAnalyzeCurrent}
            disabled={isBusy || !fileId}
            className="rounded-md border border-slate-300 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Phân tích lại
          </button>

          <button
            type="button"
            onClick={exportJson}
            disabled={!rows.length || isBusy}
            className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-4 w-4" /> Xuất JSON
          </button>

          <button
            type="button"
            onClick={exportCsv}
            disabled={!rows.length || isBusy}
            className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-4 w-4" /> Xuất CSV
          </button>
        </div>

        <div className="mb-3 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-700">
          <strong>Gợi ý:</strong> Chọn <strong>"Linh hoạt"</strong> nếu OCR không tốt hoặc tài liệu xấu. Chọn <strong>"Chặt chẽ"</strong> để giảm nhận diện nhầm.
        </div>

        <div
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => !isBusy && fileInputRef.current?.click()}
          className={`mb-4 cursor-pointer rounded-xl border-2 border-dashed bg-white px-4 py-8 text-center transition ${
            isBusy ? "border-slate-200" : "border-sky-300 hover:bg-sky-50"
          }`}
        >
          <input ref={fileInputRef} type="file" accept="application/pdf" className="hidden" onChange={onInput} />
          <FileUp className="mx-auto mb-2 h-8 w-8 text-sky-600" />
          <p className="text-sm font-semibold text-slate-700">
            {selectedFile ? selectedFile.name : "Kéo-thả hoặc bấm để chọn file PDF"}
          </p>
        </div>

        {loadingStage && (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
            <div className="mb-2 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              {loadingStage}
            </div>
            <div className="h-1.5 overflow-hidden rounded bg-amber-200">
              <div className="h-full w-1/2 animate-pulse rounded bg-amber-500" />
            </div>
          </div>
        )}

        {error && <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {success && <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{success}</div>}

        <StatsDashboard rows={rows} totalPages={totalPages} />

        {rows.length > 0 && (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_400px]">
            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-800">Danh sách từng trang</h2>
                  <p className="text-xs text-slate-500">
                    Tổng {totalPages} trang | Bạn đã chọn {suggestedCount} trang bắt đầu
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleSplit}
                  disabled={isBusy}
                  className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scissors className="h-4 w-4" />}
                  Xác nhận và Tách file
                </button>
              </div>

              <div className="max-h-[560px] overflow-auto rounded-lg border border-slate-200">
                {rows.map((row) => (
                  <div
                    key={row.page_index}
                    onMouseEnter={() => setHoveredPageIndex(row.page_index)}
                    className={`border-b border-slate-100 p-3 transition ${
                      hoveredPageIndex === row.page_index ? "bg-sky-50" : "bg-white"
                    }`}
                  >
                    <div className="mb-2 flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-800">Trang {row.page_index + 1}</p>
                        <p className="text-xs text-slate-500">Tiêu đề: {row.detected_title || "(không nhận được)"}</p>
                        <p className="text-xs text-slate-500">Số hiệu: {row.detected_number || "(không nhận được)"}</p>
                        <p className="text-xs text-slate-500">
                          Điểm: <span className="font-semibold text-slate-700">{row.start_score.toFixed(2)}</span>
                          {" "}(điểm có trọng số: {row.weighted_score.toFixed(2)} | ngưỡng: {effectiveThreshold.toFixed(2)})
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {row.is_start_page && (
                          <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-semibold text-red-700">Đề xuất tách</span>
                        )}
                        <button
                          type="button"
                          onClick={() => toggleStartPage(row.page_index)}
                          className={`rounded-md px-2 py-1 text-xs font-semibold ${
                            row.is_start_page
                              ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                          }`}
                        >
                          {row.is_start_page ? "Trang bắt đầu" : "Đánh dấu lại"}
                        </button>
                      </div>
                    </div>

                    <div className="mb-2 flex flex-wrap gap-2">
                      <AnchorBadge label="Mỏ neo 1" anchorData={row.anchor_1_emblem} />
                      <AnchorBadge label="Mỏ neo 2" anchorData={row.anchor_2_doc_number} />
                      <AnchorBadge label="Mỏ neo 3" anchorData={row.anchor_3_title} />
                      {row.emblem_type !== "none" && (
                        <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[11px] font-semibold text-purple-700">
                          Quốc huy: {row.emblem_type === "small" ? "nhỏ" : row.emblem_type === "large" ? "lớn" : row.emblem_type}
                        </span>
                      )}
                    </div>

                    <p className="line-clamp-2 text-xs text-slate-600">{row.text_preview || "Không có đoạn xem trước"}</p>
                  </div>
                ))}
              </div>
            </section>

            <aside className="rounded-xl border border-slate-200 bg-white shadow-sm" style={{ height: 640 }}>
              <PdfPreviewCard fileId={fileId} pageIndex={hoveredPageIndex} />
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
