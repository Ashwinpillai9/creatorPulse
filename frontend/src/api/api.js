import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const generateNewsletter = () => axios.post(`${API_BASE}/newsletter/generate`);
export const sendNewsletter = () => axios.post(`${API_BASE}/newsletter/send`);
export const listSources = () => axios.get(`${API_BASE}/sources`);
export const addSource = (name, url) => axios.post(`${API_BASE}/sources`, { name, url, type: "rss" });
export const ingestSource = (url) => axios.post(`${API_BASE}/sources/ingest?url=${encodeURIComponent(url)}`);
