import React, { useState, useCallback } from "react";
import styles from "./UploadZone.module.css";

export default function UploadZone({ onFileSelected, disabled }) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type === "application/pdf") onFileSelected(file);
    },
    [onFileSelected]
  );

  return (
    <div
      className={`${styles.zone} ${dragging ? styles.dragging : ""} ${disabled ? styles.disabled : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && document.getElementById("fileInput").click()}
    >
      <input
        id="fileInput"
        type="file"
        accept="application/pdf"
        hidden
        onChange={(e) => e.target.files[0] && onFileSelected(e.target.files[0])}
      />
      <span className={styles.icon}>📄</span>
      <p>Kéo thả file PDF vào đây hoặc <strong>bấm để chọn</strong></p>
      <p className={styles.hint}>Chỉ hỗ trợ file .pdf</p>
    </div>
  );
}
