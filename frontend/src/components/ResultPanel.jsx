import React, { useState } from "react";
import styles from "./ResultPanel.module.css";
import { downloadFile } from "../api";

export default function ResultPanel({ fileId, outputFiles, onReset }) {
  const [downloading, setDownloading] = useState({});
  const [errors, setErrors] = useState({});

  const handleDownload = async (name) => {
    setDownloading((prev) => ({ ...prev, [name]: true }));
    setErrors((prev) => ({ ...prev, [name]: null }));
    try {
      await downloadFile(fileId, name);
    } catch (e) {
      setErrors((prev) => ({ ...prev, [name]: "Tải thất bại" }));
    } finally {
      setDownloading((prev) => ({ ...prev, [name]: false }));
    }
  };

  return (
    <div className={styles.panel}>
      <h3>✅ Tách thành công — {outputFiles.length} file</h3>
      <ul className={styles.list}>
        {outputFiles.map((name) => (
          <li key={name}>
            <button
              onClick={() => handleDownload(name)}
              disabled={downloading[name]}
              className={styles.link}
            >
              {downloading[name] ? "⏳ Đang tải…" : `⬇ ${name}`}
            </button>
            {errors[name] && (
              <span className={styles.err}>{errors[name]}</span>
            )}
          </li>
        ))}
      </ul>
      <button className={styles.reset} onClick={onReset}>
        Tải file mới
      </button>
    </div>
  );
}
