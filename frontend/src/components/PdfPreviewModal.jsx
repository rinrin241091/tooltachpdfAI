import React, { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import styles from "./PdfPreviewModal.module.css";
import { ChevronLeft, ChevronRight, X } from "lucide-react";

// Dung PDF worker tu CDN
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.js';

export default function PdfPreviewModal({ fileUrl, startPage, endPage, onClose }) {
  const [currentPage, setCurrentPage] = useState(startPage + 1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePrev = () => {
    if (currentPage > startPage + 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < endPage + 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h3>
            Preview: Trang {startPage + 1} - {endPage + 1}
          </h3>
          <button onClick={onClose} className={styles.closeBtn}>
            <X size={20} />
          </button>
        </div>

        <div className={styles.content}>
          {error && <div className={styles.error}>{error}</div>}
          {!error && (
            <Document
              file={fileUrl}
              onLoadSuccess={() => setLoading(false)}
              onLoadError={(err) => {
                setError("Khong the tai PDF");
                console.error(err);
              }}
              loading={<div className={styles.loading}>Dang tai PDF...</div>}
            >
              <Page
                pageNumber={currentPage}
                renderTextLayer={false}
                renderAnnotationLayer={false}
                scale={1.3}
              />
            </Document>
          )}
        </div>

        <div className={styles.nav}>
          <button
            onClick={handlePrev}
            disabled={currentPage === startPage + 1}
            className={styles.btn}
          >
            <ChevronLeft size={18} /> Trang truoc
          </button>
          <span className={styles.pageNum}>
            {currentPage} / {endPage + 1}
          </span>
          <button
            onClick={handleNext}
            disabled={currentPage === endPage + 1}
            className={styles.btn}
          >
            Trang sau <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
