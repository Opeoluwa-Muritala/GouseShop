export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";

function readCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

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
  const headers = {
    "X-Session-Id": makeSessionId(),
    ...(options.headers || {}),
  };
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const csrfToken = readCookie("gouseshop_csrf");
  const method = (options.method || "GET").toUpperCase();
  if (csrfToken && !["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers["X-CSRF-Token"] = decodeURIComponent(csrfToken);
  }

  const rootUrl = API_URL.replace(/\/api\/v1\/?$/, "");
  const url = path.startsWith("http://") || path.startsWith("https://")
    ? path
    : path.startsWith("/admin")
    ? `${rootUrl}${path}`
    : `${API_URL}${path}`;
  const response = await fetch(url, { ...options, headers, credentials: "include" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    const detail = typeof error.detail === "string" ? error.detail : JSON.stringify(error.detail);
    throw new Error(`${response.status}: ${detail}`);
  }
  if (response.status === 204) return null;
  return response.json();
}
