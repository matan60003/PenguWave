import { SecurityEvent } from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 3, backoff = 300) {
  const token = localStorage.getItem("token");
  const headers = {
    ...options.headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const config = { ...options, headers };

  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url, config);
      if (!res.ok) {
        if (res.status >= 500) {
          throw new Error(`Server error ${res.status}`);
        } else {
          // Client error, parse and throw (do not retry)
          const errorData = await res.json().catch(() => ({}));
          return Promise.reject(new Error(errorData.error || `Error ${res.status}`));
        }
      }
      return res;
    } catch (err) {
      if (i === retries) throw err;
      await new Promise(resolve => setTimeout(resolve, backoff * Math.pow(2, i)));
    }
  }
  throw new Error("Unreachable");
}

export async function login(email: string, password: string) {
  const res = await fetchWithRetry(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  localStorage.setItem("token", data.token);
  return data;
}

export async function getCurrentUser() {
  const res = await fetchWithRetry(`${API_URL}/api/auth/me`);
  return res.json();
}

export async function getEvents(page = 1, limit = 25, search = "", severity = "ALL") {
  const offset = (page - 1) * limit;
  const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
  if (search) params.append("search", search);
  if (severity !== "ALL") params.append("severity", severity);
  
  const res = await fetchWithRetry(`${API_URL}/api/events?${params.toString()}`);
  return res.json();
}

export async function getUsers() {
  const res = await fetchWithRetry(`${API_URL}/api/users`);
  return res.json();
}

export async function createUser(user: { email: string; password: string; role: string }) {
  const res = await fetchWithRetry(`${API_URL}/api/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(user),
  });
  return res.json();
}

export async function deleteUser(id: string) {
  const res = await fetchWithRetry(`${API_URL}/api/users/${id}`, {
    method: "DELETE",
  });
  return res.json();
}

export async function createEvent(eventData: Omit<SecurityEvent, "id">) {
  const res = await fetchWithRetry(`${API_URL}/api/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(eventData),
  });
  return res.json();
}

export async function deleteEvent(id: string) {
  const res = await fetchWithRetry(`${API_URL}/api/events/${id}`, {
    method: "DELETE",
  });
  if (res.status === 204) return null;
  return res.json();
}
