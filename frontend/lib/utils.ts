import type { SeverityLevel } from "@/types/inspection";

/** Format an ISO timestamp to a human-readable string. */
export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

/** Text colour classes per severity — cyberpunk neon palette. */
export function severityColour(level: SeverityLevel | string | null): string {
  switch (level) {
    case "Low":      return "text-[#00ff88]";
    case "Moderate": return "text-[#facc15]";
    case "High":     return "text-[#ff8c42]";
    case "Critical": return "text-[#ff3366]";
    default:         return "text-[#6b7280]";
  }
}

/** Badge background classes per severity — neon bordered chips. */
export function severityBadgeBg(level: SeverityLevel | string | null): string {
  switch (level) {
    case "Low":
      return "bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/50 shadow-[0_0_8px_#00ff8830]";
    case "Moderate":
      return "bg-[#facc15]/10 text-[#facc15] border border-[#facc15]/50 shadow-[0_0_8px_#facc1530]";
    case "High":
      return "bg-[#ff8c42]/10 text-[#ff8c42] border border-[#ff8c42]/50 shadow-[0_0_8px_#ff8c4230]";
    case "Critical":
      return "bg-[#ff3366]/15 text-[#ff3366] border border-[#ff3366]/60 shadow-[0_0_10px_#ff336650]";
    default:
      return "bg-[#1c1c2e] text-[#6b7280] border border-[#2a2a3a]";
  }
}

/** Truncate a string to maxLen characters. */
export function truncate(s: string, maxLen = 60): string {
  return s.length > maxLen ? s.slice(0, maxLen) + "…" : s;
}

/** Recharts / chart hex colours matched to the design system. */
export const CHART_COLOURS = {
  Low: "#00ff88",
  Moderate: "#facc15",
  High: "#ff8c42",
  Critical: "#ff3366",
  bar: "#00d4ff",
  tooltipBg: "#12121a",
  tooltipBorder: "#2a2a3a",
  muted: "#6b7280",
} as const;
