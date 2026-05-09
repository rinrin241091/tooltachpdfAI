import axios from "axios";
import { saveAs } from "file-saver";

// CRA proxy chi hoat dong voi axios/fetch, KHONG proxy browser navigation.
// Dung bien nay cho tat ca download de chay vao dung cong 8000.
export const API_BASE =
  process.env.REACT_APP_API_BASE || "http://localhost:8000";

const api = axios.create({ baseURL: API_BASE });

export const uploadPDF = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const analyzePDF = (fileId) =>
  api.get(`/analyze/${fileId}`);

export const splitPDF = (fileId, breakPoints) =>
  api.post("/split", { file_id: fileId, break_points: breakPoints });

// Tai file qua axios blob (tranh CRA proxy khong forward browser navigation)
export const downloadFile = async (fileId, filename) => {
  const url = `${API_BASE}/download/${fileId}/${encodeURIComponent(filename)}`;
  const res = await axios.get(url, { responseType: "blob" });
  saveAs(res.data, filename);
};

export const cleanup = (fileId) =>
  api.delete(`/cleanup/${fileId}`);
