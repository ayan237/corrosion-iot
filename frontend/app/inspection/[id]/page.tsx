"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getInspection, resolveMediaUrl } from "@/lib/api";
import type { Inspection } from "@/types/inspection";
import SeverityBadge from "@/components/ui/SeverityBadge";
import DemoBanner from "@/components/ui/DemoBanner";
import Disclaimer from "@/components/ui/Disclaimer";
import { formatDate } from "@/lib/utils";

export default function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [ins, setIns]         = useState<Inspection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getInspection(id)
      .then(setIns)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-[#6b7280]">
        <div className="w-8 h-8 border-2 border-[#00ff88] border-t-transparent spin-cyber" />
        <p className="font-label text-xs tracking-[0.2em] uppercase cyber-cursor">
          Loading inspection
        </p>
      </div>
    );
  }

  if (error || !ins) {
    return (
      <div className="space-y-4">
        <Link
          href="/history"
          className="font-label text-[10px] tracking-[0.2em] uppercase text-[#00d4ff] hover:text-[#00ff88]"
        >
          ← Back to history
        </Link>
        <div className="cyber-card cyber-chamfer border-[#ff3366]/60 bg-[#ff3366]/10 p-6 text-[#ff3366]">
          {error ?? "Inspection not found."}
        </div>
      </div>
    );
  }

  const annotatedUrl = resolveMediaUrl(ins.annotated_image_url);
  const originalUrl  = resolveMediaUrl(ins.image_reference);

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <Link
            href="/history"
            className="font-label text-[10px] tracking-[0.2em] uppercase text-[#6b7280] hover:text-[#00d4ff] transition-colors"
          >
            ← History
          </Link>
          <p className="font-label text-[10px] tracking-[0.3em] text-[#00d4ff] uppercase mt-3 mb-1">
            &gt; record / detail
          </p>
          <h1 className="font-heading font-black tracking-wider text-xl sm:text-2xl text-[#e0e0e0] neon-text-tertiary">
            {ins.inspection_id}
          </h1>
          <p className="text-xs text-[#6b7280] mt-1 font-label tracking-wide">
            {formatDate(ins.timestamp)}
          </p>
        </div>
        <SeverityBadge level={ins.severity} size="lg" />
      </div>

      {ins.inference_mode === "demo" && <DemoBanner />}

      {/* Images */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <p className="cyber-label">Original Image</p>
          <div className="cyber-card cyber-chamfer overflow-hidden flex items-center justify-center min-h-48">
            {originalUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={originalUrl} alt="Original" className="max-h-72 w-full object-contain" />
            ) : (
              <p className="text-[#6b7280] text-sm p-4 font-label uppercase tracking-wide">
                Image not available
              </p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <p className="cyber-label">
            AI Detection{ins.inference_mode === "demo" ? " [DEMO]" : ""}
          </p>
          <div className="cyber-card cyber-chamfer overflow-hidden flex items-center justify-center min-h-48 border-[#00ff88]/20 neon-glow-sm">
            {annotatedUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={annotatedUrl} alt="Annotated" className="max-h-72 w-full object-contain" />
            ) : (
              <p className="text-[#6b7280] text-sm p-4 font-label uppercase tracking-wide">
                No annotations available
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Main data grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="cyber-card cyber-chamfer p-5 space-y-4">
          <h2 className="cyber-label text-[#00ff88]">Detection Results</h2>

          <Row label="Status">
            <span className={ins.detected ? "text-[#ff8c42]" : "text-[#00ff88]"}>
              {ins.detected ? "Corrosion Detected" : "No Corrosion Detected"}
            </span>
          </Row>

          {ins.confidence != null && (
            <Row label="Top Confidence">
              <span className="font-mono">{(ins.confidence * 100).toFixed(1)}%</span>
            </Row>
          )}

          <Row label="Affected Area (est.)">
            <span className="font-mono text-[#00d4ff]">{ins.affected_area.toFixed(2)}%</span>
          </Row>

          <Row label="Severity">
            <SeverityBadge level={ins.severity} />
          </Row>

          {ins.severity_reasoning && (
            <p className="text-xs text-[#6b7280] border-t border-[#2a2a3a] pt-3">
              {ins.severity_reasoning}
            </p>
          )}
        </div>

        <div className="cyber-card-holo cyber-chamfer p-5 space-y-4">
          <h2 className="cyber-label text-[#00d4ff]">Environmental Data</h2>

          <Row label="Temperature">
            <span className="font-mono">
              {ins.temperature != null ? `${ins.temperature} °C` : "—"}
            </span>
          </Row>

          <Row label="Humidity">
            <span className="font-mono">
              {ins.humidity != null ? `${ins.humidity}%` : "—"}
            </span>
          </Row>

          {ins.environmental_note && (
            <p className="text-xs text-[#6b7280] border-t border-[#2a2a3a] pt-3">
              {ins.environmental_note}
            </p>
          )}

          <div className="border-t border-[#2a2a3a] pt-3 space-y-3">
            <h2 className="cyber-label">Metadata</h2>
            <Row label="Device ID">
              <span className="font-mono text-xs">{ins.device_id ?? "—"}</span>
            </Row>
            <Row label="Inference Mode">
              <span
                className={`text-xs font-mono uppercase tracking-wider ${
                  ins.inference_mode === "demo" ? "text-[#ff00ff]" : "text-[#00ff88]"
                }`}
              >
                {ins.inference_mode}
              </span>
            </Row>
            <Row label="Timestamp">
              <span className="font-mono text-xs text-[#6b7280]">
                {ins.timestamp}
              </span>
            </Row>
          </div>
        </div>
      </div>

      {/* Detections table */}
      {ins.detections.length > 0 && (
        <div className="cyber-card-terminal cyber-chamfer overflow-hidden">
          <div className="px-5 py-3 border-b border-[#2a2a3a]">
            <h2 className="cyber-label text-[#00ff88]">
              &gt; Raw Detections ({ins.detections.length})
            </h2>
          </div>
          <table className="cyber-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Class</th>
                <th>Confidence</th>
                <th>Bounding Box [x1, y1, x2, y2]</th>
              </tr>
            </thead>
            <tbody>
              {ins.detections.map((d, i) => (
                <tr key={i}>
                  <td className="text-[#6b7280] text-xs">{i + 1}</td>
                  <td className="capitalize font-mono text-xs text-[#e0e0e0]">
                    {d.class}
                  </td>
                  <td className="font-mono text-xs text-[#00d4ff]">
                    {(d.confidence * 100).toFixed(1)}%
                  </td>
                  <td className="font-mono text-xs text-[#6b7280]">
                    [{d.bounding_box.map((v) => Math.round(v)).join(", ")}]
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Recommendation / AI Solution */}
      {ins.ai_solution ? (
        <div className="cyber-card-terminal cyber-chamfer p-6 space-y-5 border-[#00d4ff]/40 neon-glow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#2a2a3a] pb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#00ff88] animate-pulse" />
              <h2 className="cyber-label text-[#00d4ff] text-sm tracking-widest">
                &gt; AI Predicted Maintenance Solution
              </h2>
            </div>
            <div className="flex items-center gap-2">
              {ins.ai_solution.estimated_urgency && (
                <span className="text-[10px] font-mono px-2 py-0.5 border border-[#ff00ff]/60 bg-[#ff00ff]/10 text-[#ff00ff] uppercase tracking-wider rounded">
                  Urgency: {ins.ai_solution.estimated_urgency}
                </span>
              )}
              <span className="text-[10px] font-mono px-2 py-0.5 border border-[#00ff88]/60 bg-[#00ff88]/10 text-[#00ff88] uppercase tracking-wider rounded">
                Gemini AI
              </span>
            </div>
          </div>

          <div className="space-y-1">
            <p className="text-xs uppercase font-label tracking-wider text-[#6b7280]">
              Executive Action Summary
            </p>
            <p className="text-sm text-[#e0e0e0] leading-relaxed">
              {ins.ai_solution.summary}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {/* Immediate Actions */}
            {ins.ai_solution.immediate_actions && ins.ai_solution.immediate_actions.length > 0 && (
              <div className="cyber-card cyber-chamfer p-4 space-y-2 border-[#ff3366]/30 bg-[#ff3366]/5">
                <div className="flex items-center gap-2 text-[#ff3366]">
                  <span className="text-sm">🚨</span>
                  <h3 className="cyber-label text-xs uppercase tracking-wider">
                    Immediate Actions
                  </h3>
                </div>
                <ul className="space-y-1.5 list-disc list-inside text-xs text-[#d1d5db]">
                  {ins.ai_solution.immediate_actions.map((act, idx) => (
                    <li key={idx} className="leading-snug">{act}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Surface Preparation */}
            {ins.ai_solution.surface_preparation && ins.ai_solution.surface_preparation.length > 0 && (
              <div className="cyber-card cyber-chamfer p-4 space-y-2 border-[#ff8c42]/30 bg-[#ff8c42]/5">
                <div className="flex items-center gap-2 text-[#ff8c42]">
                  <span className="text-sm">🛠</span>
                  <h3 className="cyber-label text-xs uppercase tracking-wider">
                    Surface Preparation
                  </h3>
                </div>
                <ul className="space-y-1.5 list-disc list-inside text-xs text-[#d1d5db]">
                  {ins.ai_solution.surface_preparation.map((prep, idx) => (
                    <li key={idx} className="leading-snug">{prep}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Treatment & Protective Coating */}
            {ins.ai_solution.treatment_and_coating && ins.ai_solution.treatment_and_coating.length > 0 && (
              <div className="cyber-card cyber-chamfer p-4 space-y-2 border-[#00d4ff]/30 bg-[#00d4ff]/5">
                <div className="flex items-center gap-2 text-[#00d4ff]">
                  <span className="text-sm">🛡</span>
                  <h3 className="cyber-label text-xs uppercase tracking-wider">
                    Treatment & Coating
                  </h3>
                </div>
                <ul className="space-y-1.5 list-disc list-inside text-xs text-[#d1d5db]">
                  {ins.ai_solution.treatment_and_coating.map((treat, idx) => (
                    <li key={idx} className="leading-snug">{treat}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Preventive Schedule */}
            {ins.ai_solution.preventive_schedule && (
              <div className="cyber-card cyber-chamfer p-4 space-y-2 border-[#00ff88]/30 bg-[#00ff88]/5">
                <div className="flex items-center gap-2 text-[#00ff88]">
                  <span className="text-sm">📅</span>
                  <h3 className="cyber-label text-xs uppercase tracking-wider">
                    Preventive Schedule
                  </h3>
                </div>
                <p className="text-xs text-[#d1d5db] leading-relaxed">
                  {ins.ai_solution.preventive_schedule}
                </p>
              </div>
            )}
          </div>

          <div className="border-t border-[#2a2a3a] pt-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-[#6b7280]">
            <p className="italic">{ins.recommendation_disclaimer}</p>
            {ins.ai_solution.model_used && (
              <span className="font-mono text-[#00d4ff]/80">
                Model: {ins.ai_solution.model_used}
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="cyber-card-terminal cyber-chamfer p-5 space-y-2">
          <h2 className="cyber-label text-[#00ff88]">
            &gt; Maintenance Recommendation
          </h2>
          <p className="text-sm text-[#e0e0e0]">{ins.recommendation}</p>
          <p className="text-xs text-[#6b7280] italic">{ins.recommendation_disclaimer}</p>
        </div>
      )}

      <Disclaimer />
    </div>
  );
}

function Row({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-xs text-[#6b7280] flex-shrink-0 font-label tracking-wide uppercase">
        {label}
      </span>
      <span className="text-sm text-[#e0e0e0] text-right">{children}</span>
    </div>
  );
}
