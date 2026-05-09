import React from "react";
import styles from "./PageList.module.css";

export default function PageList({ pages, breakPoints, onToggleBreak }) {
  return (
    <div className={styles.container}>
      <h3>Danh sách trang ({pages.length} trang)</h3>
      <p className={styles.hint}>
        Các trang được đánh dấu <span className={styles.badgeTitle}>Tiêu đề</span> là điểm ngắt gợi ý.
        Bấm vào trang để thêm / xóa điểm ngắt.
      </p>
      <ul className={styles.list}>
        {pages.map((page) => {
          const isBreak = breakPoints.includes(page.page_number);
          const isFirst = page.page_number === 0;
          return (
            <li
              key={page.page_number}
              className={`${styles.item} ${isBreak ? styles.break : ""} ${isFirst ? styles.first : ""}`}
              onClick={() => !isFirst && onToggleBreak(page.page_number)}
              title={isFirst ? "Trang đầu luôn là điểm bắt đầu" : "Bấm để bật/tắt điểm ngắt"}
            >
              <span className={styles.pageNum}>Trang {page.page_number + 1}</span>

              {page.is_title && (
                <span className={styles.badgeTitle}>Tiêu đề</span>
              )}
              {isBreak && (
                <span className={styles.badgeBreak}>✂ Ngắt tại đây</span>
              )}

              <p className={styles.preview}>{page.text_preview || "(Không có chữ)"}</p>

              <span className={styles.conf}>
                Độ tin cậy OCR: {(page.confidence * 100).toFixed(1)}%
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
