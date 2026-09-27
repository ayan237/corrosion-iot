/**
 * API client — thin wrapper around fetch.
 * All backend calls go through these functions so the URL is centralised.
 */
import type {
  HealthStatus,
  HistoryResponse,
  Inspection,
  Statistics,
} from "@/types/inspection";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    // Don't cache inspection data
    cache: "no-store",
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body?.detail ?? body?.message ?? message;
      if (typeof message === "object") message = JSON.stringify(message);
    } catch {
      // ignore parse error
    }
    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

// ── Health ─────────────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/api/health");
}

// ── Inspection ─────────────────────────────────────────────────────────────

export interface InspectionPayload {
  image: File;
  temperature?: number | null;
  humidity?: number | null;
  device_id?: string | null;
}

export async function runInspection(
  payload: InspectionPayload
): Promise<Inspection> {
  const form = new FormData();
  form.append("image", payload.image);
  if (payload.temperature != null)
    form.append("temperature", String(payload.temperature));
  if (payload.humidity != null)
    form.append("humidity", String(payload.humidity));
  if (payload.device_id)
    form.append("device_id", payload.device_id);

  return request<Inspection>("/api/inspection", { method: "POST", body: form });
}

export async function getInspection(id: string): Promise<Inspection> {
  return request<Inspection>(`/api/inspection/${id}`);
}

// ── History ────────────────────────────────────────────────────────────────

export interface HistoryParams {
  page?: number;
  page_size?: number;
  severity?: string;
  detected?: boolean;
  date_from?: string;
  date_to?: string;
}

export async function getHistory(
  params: HistoryParams = {}
): Promise<HistoryResponse> {
  const q = new URLSearchParams();
  if (params.page) q.set("page", String(params.page));
  if (params.page_size) q.set("page_size", String(params.page_size));
  if (params.severity) q.set("severity", params.severity);
  if (params.detected != null) q.set("detected", String(params.detected));
  if (params.date_from) q.set("date_from", params.date_from);
  if (params.date_to) q.set("date_to", params.date_to);
  const qs = q.toString() ? `?${q.toString()}` : "";
  return request<HistoryResponse>(`/api/history${qs}`);
}

// ── Statistics ─────────────────────────────────────────────────────────────

export async function getStatistics(): Promise<Statistics> {
  return request<Statistics>("/api/statistics");
}

// ── Utilities ──────────────────────────────────────────────────────────────

/** Resolve a backend-relative URL to an absolute URL for <img> tags. */
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${BASE}${path}`;
}
