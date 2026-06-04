import { SecurityEvent } from "./types";

const API_URL = "http://localhost:3001";

async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 3, backoff = 300) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, options);
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
      if (i === retries - 1) throw err;
      await new Promise(resolve => setTimeout(resolve, backoff * Math.pow(2, i)));
    }
  }
  return fetch(url, options);
}

export async function login(email: string, password: string) {
  console.log("Login attempt:", email, password);
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
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No token");
  const res = await fetchWithRetry(`${API_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

export async function getEvents() {
  const token = localStorage.getItem("token");
  const res = await fetchWithRetry(`${API_URL}/api/events`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

export async function getUsers() {
  const token = localStorage.getItem("token");
  const res = await fetchWithRetry(`${API_URL}/api/users`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

export async function createUser(user: { email: string; password: string; role: string }) {
  const token = localStorage.getItem("token");
  const res = await fetchWithRetry(`${API_URL}/api/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(user),
  });
  return res.json();
}

export async function deleteUser(id: string) {
  const token = localStorage.getItem("token");
  const res = await fetchWithRetry(`${API_URL}/api/users/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

export async function createEvent(eventData: Omit<SecurityEvent, "id" | "timestamp">) {
  const token = localStorage.getItem("token");
  const res = await fetchWithRetry(`${API_URL}/api/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(eventData),
  });
  return res.json();
}

export async function deleteEvent(id: string) {
  const token = localStorage.getItem("token");
  const res = await fetchWithRetry(`${API_URL}/api/events/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 204) return null;
  return res.json().catch(() => null);
}
