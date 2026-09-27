"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { getStatistics, getHistory, getHealth } from "@/lib/api";
import type { Statistics, HealthStatus, Inspection } from "@/types/inspection";
import StatCard from "@/components/ui/StatCard";
import SeverityBadge from "@/components/ui/SeverityBadge";
import { formatDate, CHART_COLOURS } from "@/lib/utils";

export default function Dashboard() {
  const [stats, setStats]     = useState<Statistics | null>(null);
  const [health, setHealth]   = useState<HealthStatus | null>(null);
  const [recent, setRecent]   = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getStatistics(), getHealth(), getHistory({ page: 1, page_size: 5 })])
      .then(([s, h, hist]) => {
        setStats(s);
        setHealth(h);
        setRecent(hist.items);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-[#6b7280]">
        <div className="w-8 h-8 border-2 border-[#00ff88] border-t-transparent spin-cyber" />
        <p className="font-label text-xs tracking-[0.2em] uppercase cyber-cursor">
          Syncing terminal
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cyber-card cyber-chamfer border-[#ff3366]/60 bg-[#ff3366]/10 p-6 mt-4 neon-glow-secondary">
        <p className="font-heading font-bold uppercase tracking-widest text-[#ff3366]">
          Link Failure
        </p>
        <p className="text-sm mt-2 text-[#e0e0e0]">{error}</p>
        <p className="text-sm mt-3 text-[#6b7280]">
          Bring the FastAPI node online:{" "}
          <code className="bg-[#0a0a0f] px-1.5 py-0.5 text-[#00d4ff] text-xs">
            uvicorn app.main:app --reload --port 8000
          </code>
        </p>
      </div>
    );
  }

  const pieData = Object.entries(stats?.severity_distribution ?? {}).map(
    ([name, value]) => ({ name, value })
  );
  const timelineData = stats?.inspection_timeline ?? [];

  return (
    <div className="space-y-8">
      {/* Hero / brand */}
      <section className="relative overflow-hidden cyber-card-holo cyber-chamfer p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div className="max-w-2xl">
            <p className="font-label text-[10px] tracking-[0.3em] text-[#00d4ff] uppercase mb-3">
              &gt; remote_inspection_feed
            </p>
            <h1 className="font-heading font-black uppercase tracking-[0.12em] text-4xl sm:text-5xl lg:text-6xl cyber-glitch-text text-[#e0e0e0]">
              CORROSION
              <br />
              <span className="neon-text">INSPECT</span>
            </h1>
            <p className="mt-4 text-sm sm:text-base text-[#6b7280] max-w-md leading-relaxed cyber-cursor">
              AI visual scan · env context · severity terminal
            </p>
          </div>
          <Link
            href="/inspect"
            className="cyber-btn cyber-btn-glitch cyber-chamfer-sm self-start lg:self-end shrink-0"
          >
            + New Inspection
          </Link>
        </div>
      </section>

      {/* Inference mode badge */}
      {health && (
        <div
          className={`inline-flex items-center gap-2 font-label text-[10px] tracking-[0.2em] uppercase px-3 py-2 cyber-chamfer-sm border ${
            health.inference_mode === "demo"
              ? "bg-[#ff00ff]/10 border-[#ff00ff]/50 text-[#ff00ff] neon-glow-secondary"
              : "bg-[#00ff88]/10 border-[#00ff88]/50 text-[#00ff88] neon-glow-sm"
          }`}
        >
          <span
            className={`w-2 h-2 status-dot-live ${
              health.inference_mode === "demo" ? "bg-[#ff00ff]" : "bg-[#00ff88]"
            }`}
          />
          {health.inference_mode === "demo"
            ? "Demo Mode — simulated detections"
            : "Live Mode — real AI inference"}{" "}
          · DB: {health.database}
        </div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard label="Total Inspections" value={stats?.total_inspections ?? 0} />
        <StatCard
          label="Corrosion Detected"
          value={stats?.corrosion_detected ?? 0}
          accent="text-[#ff8c42]"
        />
        <StatCard
          label="No Corrosion"
          value={stats?.no_corrosion ?? 0}
          accent="neon-text"
        />
        <StatCard
          label="High / Critical"
          value={stats?.high_critical_cases ?? 0}
          accent="text-[#ff3366]"
        />
        <StatCard
          label="Detection Rate"
          value={`${stats?.detection_rate ?? 0}%`}
          accent="text-[#facc15]"
        />
        <StatCard
          label="Avg Affected Area"
          value={`${stats?.avg_affected_area ?? 0}%`}
          accent="neon-text-tertiary"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 -skew-y-[0.4deg]">
        <div className="cyber-card cyber-chamfer p-4 skew-y-[0.4deg]">
          <h2 className="cyber-label mb-3 text-[#00ff88]">Severity Distribution</h2>
          {pieData.length === 0 ? (
            <p className="text-[#6b7280] text-sm py-8 text-center font-label tracking-widest uppercase">
              No data yet
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  dataKey="value"
                  paddingAngle={3}
                >
                  {pieData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={
                        CHART_COLOURS[entry.name as keyof typeof CHART_COLOURS] ??
                        "#6b7280"
                      }
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: CHART_COLOURS.tooltipBg,
                    border: `1px solid ${CHART_COLOURS.tooltipBorder}`,
                    borderRadius: 0,
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#e0e0e0" }}
                />
                <Legend
                  formatter={(value) => (
                    <span style={{ color: "#6b7280", fontSize: 11, letterSpacing: "0.1em" }}>
                      {value}
                    </span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="cyber-card cyber-chamfer p-4 skew-y-[0.4deg]">
          <h2 className="cyber-label mb-3 text-[#00d4ff]">Inspections (Last 30 Days)</h2>
          {timelineData.length === 0 ? (
            <p className="text-[#6b7280] text-sm py-8 text-center font-label tracking-widest uppercase">
              No data yet
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={timelineData} margin={{ top: 4, right: 4, bottom: 4, left: -20 }}>
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: "#6b7280" }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    background: CHART_COLOURS.tooltipBg,
                    border: `1px solid ${CHART_COLOURS.tooltipBorder}`,
                    borderRadius: 0,
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#e0e0e0" }}
                  cursor={{ fill: "rgba(0,255,136,0.05)" }}
                />
                <Bar dataKey="count" fill={CHART_COLOURS.bar} radius={[0, 0, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent inspections — terminal variant */}
      <div className="cyber-card-terminal cyber-chamfer overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#2a2a3a]">
          <h2 className="cyber-label text-[#00ff88]">
            &gt; Recent Inspections
          </h2>
          <Link
            href="/history"
            className="font-label text-[10px] tracking-[0.2em] uppercase text-[#00d4ff] hover:text-[#00ff88] transition-colors"
          >
            View all →
          </Link>
        </div>

        {recent.length === 0 ? (
          <p className="text-[#6b7280] text-sm p-6 text-center font-label tracking-wide">
            No inspections yet.{" "}
            <Link href="/inspect" className="text-[#00ff88] hover:underline">
              Run the first one →
            </Link>
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="cyber-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Date</th>
                  <th>Detection</th>
                  <th>Severity</th>
                  <th>Area</th>
                  <th>Device</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((ins) => (
                  <tr key={ins.inspection_id}>
                    <td>
                      <Link
                        href={`/inspection/${ins.inspection_id}`}
                        className="text-[#00d4ff] hover:text-[#00ff88] font-mono text-xs transition-colors"
                      >
                        {ins.inspection_id}
                      </Link>
                    </td>
                    <td className="text-[#6b7280] text-xs">
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
                    <td className="text-[#e0e0e0] font-mono text-xs">
                      {ins.affected_area.toFixed(1)}%
                    </td>
                    <td className="text-[#6b7280] text-xs">
                      {ins.device_id ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
