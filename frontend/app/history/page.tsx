"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { getHistory } from "@/lib/api";
import type { HistoryResponse, Inspection } from "@/types/inspection";
import SeverityBadge from "@/components/ui/SeverityBadge";
import { formatDate } from "@/lib/utils";

const SEVERITY_OPTIONS = ["", "Low", "Moderate", "High", "Critical"];
const PAGE_SIZE = 15;

export default function HistoryPage() {
  const [data, setData]           = useState<HistoryResponse | null>(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);

  const [severity, setSeverity]   = useState("");
  const [detected, setDetected]   = useState<string>("");
  const [dateFrom, setDateFrom]   = useState("");
  const [dateTo, setDateTo]       = useState("");
  const [page, setPage]           = useState(1);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getHistory({
        page,
        page_size: PAGE_SIZE,
        severity:  severity  || undefined,
        detected:  detected !== "" ? detected === "true" : undefined,
        date_from: dateFrom  || undefined,
        date_to:   dateTo    || undefined,
      });
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load history.");
    } finally {
      setLoading(false);
    }
  }, [page, severity, detected, dateFrom, dateTo]);

  useEffect(() => { fetchData(); }, [fetchData]);

  function applyFilters() {
    setPage(1);
    fetchData();
  }

  function resetFilters() {
    setSeverity(""); setDetected(""); setDateFrom(""); setDateTo("");
    setPage(1);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="font-label text-[10px] tracking-[0.3em] text-[#00d4ff] uppercase mb-2">
            &gt; archive / query
          </p>
          <h1 className="font-heading font-black uppercase tracking-[0.1em] text-3xl sm:text-4xl text-[#e0e0e0]">
            Inspection <span className="neon-text">History</span>
          </h1>
          <p className="text-sm text-[#6b7280] mt-2 font-label tracking-wide">
            {data
              ? `${data.total} inspection${data.total !== 1 ? "s" : ""} total`
              : "Loading…"}
          </p>
        </div>
        <Link
          href="/inspect"
          className="cyber-btn cyber-btn-glitch cyber-chamfer-sm self-start shrink-0"
        >
          + New Inspection
        </Link>
      </div>

      {/* Filter bar */}
      <div className="cyber-card cyber-chamfer p-4">
        <div className="flex flex-wrap gap-3 items-end">
          <label className="flex flex-col gap-1.5 min-w-[120px]">
            <span className="cyber-label">Severity</span>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="cyber-select cyber-chamfer-sm"
            >
              {SEVERITY_OPTIONS.map((s) => (
                <option key={s} value={s}>{s || "All"}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1.5 min-w-[120px]">
            <span className="cyber-label">Detection</span>
            <select
              value={detected}
              onChange={(e) => setDetected(e.target.value)}
              className="cyber-select cyber-chamfer-sm"
            >
              <option value="">All</option>
              <option value="true">Detected</option>
              <option value="false">Not Detected</option>
            </select>
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="cyber-label">From</span>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="cyber-select cyber-chamfer-sm text-[#e0e0e0] [color-scheme:dark]"
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="cyber-label">To</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="cyber-select cyber-chamfer-sm text-[#e0e0e0] [color-scheme:dark]"
            />
          </label>

          <div className="flex gap-2 pb-0.5">
            <button
              type="button"
              onClick={applyFilters}
              className="cyber-btn cyber-chamfer-sm !min-h-[40px] !py-1.5 !px-4 !text-xs"
            >
              Apply
            </button>
            <button
              type="button"
              onClick={resetFilters}
              className="cyber-btn cyber-btn-outline cyber-chamfer-sm !min-h-[40px] !py-1.5 !px-4 !text-xs"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="cyber-card-terminal cyber-chamfer overflow-hidden">
        {error && (
          <div className="bg-[#ff3366]/10 border-b border-[#ff3366]/50 text-[#ff3366] px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="cyber-table">
            <thead>
              <tr>
                <th>Inspection ID</th>
                <th>Date</th>
                <th>Detection</th>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Affected Area</th>
                <th>Temp</th>
                <th>Humidity</th>
                <th>Device</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center py-10 text-[#6b7280] text-sm font-label tracking-[0.2em] uppercase">
                    <span className="cyber-cursor">Loading</span>
                  </td>
                </tr>
              ) : !data || data.items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-10 text-[#6b7280] text-sm font-label tracking-wide uppercase">
                    No inspections match the current filters
                  </td>
                </tr>
              ) : (
                data.items.map((ins) => (
                  <HistoryRow key={ins.inspection_id} ins={ins} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-3 text-sm">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="cyber-btn cyber-btn-outline cyber-chamfer-sm !min-h-[40px] !py-1.5 !px-4 !text-xs disabled:opacity-40"
          >
            ← Prev
          </button>
          <span className="text-[#6b7280] text-xs font-label tracking-[0.15em] uppercase">
            Page {page} of {data.pages} ({data.total} total)
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
            disabled={page === data.pages}
            className="cyber-btn cyber-btn-outline cyber-chamfer-sm !min-h-[40px] !py-1.5 !px-4 !text-xs disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

function HistoryRow({ ins }: { ins: Inspection }) {
  return (
    <tr>
      <td>
        <Link
          href={`/inspection/${ins.inspection_id}`}
          className="text-[#00d4ff] hover:text-[#00ff88] font-mono text-xs transition-colors"
        >
          {ins.inspection_id}
        </Link>
      </td>
      <td className="text-[#6b7280] text-xs whitespace-nowrap">
        {formatDate(ins.timestamp)}
      </td>
      <td>
        <span
          className={`text-xs font-medium uppercase tracking-wider ${
            ins.detected ? "text-[#ff8c42]" : "text-[#00ff88]"
          }`}
        >
          {ins.detected ? "Detected" : "None"}
        </span>
      </td>
      <td>
        <SeverityBadge level={ins.severity} size="sm" />
      </td>
      <td className="font-mono text-xs text-[#e0e0e0]">
        {ins.confidence != null ? `${(ins.confidence * 100).toFixed(0)}%` : "—"}
      </td>
      <td className="font-mono text-xs text-[#e0e0e0]">
        {ins.affected_area != null ? `${ins.affected_area.toFixed(1)}%` : "—"}
      </td>
      <td className="font-mono text-xs text-[#6b7280]">
        {ins.temperature != null ? `${ins.temperature}°C` : "—"}
      </td>
      <td className="font-mono text-xs text-[#6b7280]">
        {ins.humidity != null ? `${ins.humidity}%` : "—"}
      </td>
      <td className="text-[#6b7280] text-xs">
        {ins.device_id ?? "—"}
      </td>
    </tr>
  );
}
