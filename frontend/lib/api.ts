import type { CrawlRun, Match, Notice, Preference, Profile, Stats, User } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "jobradar_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function errorText(payload: { detail?: unknown }): string {
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => (item && typeof item === "object" && "msg" in item ? String(item.msg) : String(item)))
      .join(", ");
  }
  return "Có lỗi khi gọi API";
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (response.status === 401 && path !== "/auth/login" && path !== "/auth/register") {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
  }
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: unknown };
    throw new Error(errorText(payload));
  }
  if (response.status === 204) return undefined as T;
  const type = response.headers.get("content-type") || "";
  if (!type.includes("application/json")) return undefined as T;
  return response.json() as Promise<T>;
}

export const sourceLabel: Record<string, string> = {
  vietnamworks: "VietnamWorks",
  topcv: "TopCV",
  linkedin: "LinkedIn",
  sample: "Tin mẫu",
};

export const statusLabel: Record<Match["status"], string> = {
  new: "Mới",
  viewed: "Đã xem",
  saved: "Đã lưu",
  applied: "Đã apply",
};

export function formatWhen(value: string | null): string {
  if (!value) return "";
  return new Intl.DateTimeFormat("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" }).format(
    new Date(value),
  );
}

export type { CrawlRun, Match, Notice, Preference, Profile, Stats, User };
