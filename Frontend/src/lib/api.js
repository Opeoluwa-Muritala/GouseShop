export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";

export function makeSessionId() {
  const key = "gouseshop_session_id";
  let value = localStorage.getItem(key);
  if (!value) {
    value = crypto.randomUUID ? crypto.randomUUID() : `guest-${Date.now()}`;
    localStorage.setItem(key, value);
  }
  return value;
}

export async function api(path, options = {}) {
  const token = localStorage.getItem("gouseshop_token");
  const headers = {
    "X-Session-Id": makeSessionId(),
    ...(options.headers || {}),
  };
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    const detail = typeof error.detail === "string" ? error.detail : JSON.stringify(error.detail);
    throw new Error(`${response.status}: ${detail}`);
  }
  if (response.status === 204) return null;
  return response.json();
}
