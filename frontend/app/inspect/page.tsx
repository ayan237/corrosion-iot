"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { runInspection, resolveMediaUrl } from "@/lib/api";
import type { Inspection } from "@/types/inspection";
import SeverityBadge from "@/components/ui/SeverityBadge";
import DemoBanner from "@/components/ui/DemoBanner";
import Disclaimer from "@/components/ui/Disclaimer";

export default function InspectPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile]           = useState<File | null>(null);
  const [preview, setPreview]     = useState<string | null>(null);
  const [temperature, setTemp]    = useState("");
  const [humidity, setHumidity]   = useState("");
  const [deviceId, setDeviceId]   = useState("");
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState<Inspection | null>(null);
  const [error, setError]         = useState<string | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setResult(null);
    setError(null);
    if (f) {
      setPreview(URL.createObjectURL(f));
    } else {
      setPreview(null);
    }
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0] ?? null;
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) { setError("Please select an image."); return; }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await runInspection({
        image: file,
        temperature: temperature ? parseFloat(temperature) : null,
        humidity:    humidity    ? parseFloat(humidity)    : null,
        device_id:   deviceId   || null,
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Inspection failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <p className="font-label text-[10px] tracking-[0.3em] text-[#00d4ff] uppercase mb-2">
          &gt; uplink / new_scan
        </p>
        <h1 className="font-heading font-black uppercase tracking-[0.1em] text-3xl sm:text-4xl text-[#e0e0e0]">
          New <span className="neon-text">Inspection</span>
        </h1>
        <p className="text-sm text-[#6b7280] mt-2 cyber-cursor">
          Upload a corrosion image and enter sensor readings
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: image drop zone + sensor fields */}
          <div className="space-y-4">
            <div
              onClick={() => fileRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className="relative border-2 border-dashed border-[#2a2a3a] hover:border-[#00ff88] cyber-chamfer p-6 cursor-pointer transition-all min-h-[200px] flex flex-col items-center justify-center gap-2 bg-[#12121a]/50 hover:neon-glow-sm"
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") fileRef.current?.click();
              }}
            >
              {preview ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-48 object-contain border border-[#2a2a3a]"
                />
              ) : (
                <>
                  <span className="text-3xl text-[#00ff88] neon-text" aria-hidden>
                    ⬡
                  </span>
                  <p className="text-sm text-[#6b7280] text-center font-label tracking-wide uppercase">
                    Drop image or click to browse
                  </p>
                  <p className="text-[10px] text-[#2a2a3a] font-label tracking-[0.2em] uppercase">
                    JPG · PNG · WEBP · max 10 MB
                  </p>
                </>
              )}
              {file && (
                <p className="text-xs text-[#00d4ff] mt-1 font-mono">{file.name}</p>
              )}
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <label className="flex flex-col gap-1.5">
                <span className="cyber-label">Temperature (°C)</span>
                <div className="cyber-input-wrap cyber-chamfer-sm">
                  <input
                    type="number"
                    step="0.1"
                    placeholder="e.g. 31.4"
                    value={temperature}
                    onChange={(e) => setTemp(e.target.value)}
                    className="cyber-input cyber-chamfer-sm"
                  />
                </div>
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="cyber-label">Humidity (%)</span>
                <div className="cyber-input-wrap cyber-chamfer-sm">
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    placeholder="e.g. 72"
                    value={humidity}
                    onChange={(e) => setHumidity(e.target.value)}
                    className="cyber-input cyber-chamfer-sm"
                  />
                </div>
              </label>
            </div>

            <label className="flex flex-col gap-1.5">
              <span className="cyber-label">Device ID (optional)</span>
              <div className="cyber-input-wrap cyber-chamfer-sm">
                <input
                  type="text"
                  placeholder="e.g. CAM_001"
                  value={deviceId}
                  onChange={(e) => setDeviceId(e.target.value)}
                  maxLength={64}
                  className="cyber-input cyber-chamfer-sm"
                />
              </div>
            </label>

            <button
              type="submit"
              disabled={loading || !file}
              className="w-full cyber-btn cyber-btn-glitch cyber-chamfer-sm"
            >
              {loading ? "Running Inspection…" : "Run Inspection"}
            </button>

            {error && (
              <div className="border border-[#ff3366]/60 bg-[#ff3366]/10 text-[#ff3366] cyber-chamfer-sm px-3 py-2 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Right: result panel */}
          <div className="space-y-4">
            {loading && (
              <div className="cyber-card-terminal cyber-chamfer p-8 flex flex-col items-center gap-3 text-[#6b7280]">
                <div className="w-8 h-8 border-2 border-[#00ff88] border-t-transparent spin-cyber" />
                <p className="text-sm font-label tracking-[0.2em] uppercase cyber-cursor">
                  Analysing image
                </p>
              </div>
            )}

            {result && !loading && (
              <ResultPanel result={result} />
            )}

            {!result && !loading && (
              <div className="cyber-card-holo cyber-chamfer p-8 flex flex-col items-center gap-2 text-[#6b7280]">
                <span className="text-3xl text-[#2a2a3a]" aria-hidden>◈</span>
                <p className="text-sm font-label tracking-wide uppercase text-center">
                  Results will appear here after inspection
                </p>
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}

function ResultPanel({ result }: { result: Inspection }) {
  const annotatedUrl = resolveMediaUrl(result.annotated_image_url);

  return (
    <div className="space-y-4">
      {result.inference_mode === "demo" && <DemoBanner />}

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <p className="cyber-label">Original</p>
          {result.image_reference ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={resolveMediaUrl(result.image_reference) ?? ""}
              alt="Original"
              className="w-full border border-[#2a2a3a] object-contain max-h-40"
            />
          ) : (
            <div className="w-full h-40 bg-[#12121a] border border-[#2a2a3a] flex items-center justify-center text-[#6b7280] text-xs">
              No image
            </div>
          )}
        </div>
        <div className="space-y-1">
          <p className="cyber-label">
            AI Detection{result.inference_mode === "demo" ? " [DEMO]" : ""}
          </p>
          {annotatedUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={annotatedUrl}
              alt="Annotated"
              className="w-full border border-[#00ff88]/30 object-contain max-h-40 neon-glow-sm"
            />
          ) : (
            <div className="w-full h-40 bg-[#12121a] border border-[#2a2a3a] flex items-center justify-center text-[#6b7280] text-xs">
              No annotation
            </div>
          )}
        </div>
      </div>

      <div className="cyber-card cyber-chamfer p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="cyber-label">Detection</span>
          <span className={`text-sm font-semibold uppercase tracking-wider ${result.detected ? "text-[#ff8c42]" : "text-[#00ff88]"}`}>
            {result.detected ? "Corrosion Detected" : "No Corrosion Detected"}
          </span>
        </div>

        {result.detected && result.confidence != null && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#6b7280]">Top Confidence</span>
            <span className="font-mono text-sm text-[#e0e0e0]">
              {(result.confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}

        <div className="flex items-center justify-between">
          <span className="text-xs text-[#6b7280]">Affected Area (est.)</span>
          <span className="font-mono text-sm text-[#00d4ff]">
            {result.affected_area.toFixed(1)}%
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-[#6b7280]">Severity</span>
          <SeverityBadge level={result.severity} />
        </div>

        {(result.temperature != null || result.humidity != null) && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#6b7280]">Environment</span>
            <span className="text-xs text-[#e0e0e0] font-mono">
              {result.temperature != null ? `${result.temperature}°C` : "—"}{" "}
              /{" "}
              {result.humidity != null ? `${result.humidity}%` : "—"}
            </span>
          </div>
        )}

        {result.environmental_note && (
          <p className="text-xs text-[#6b7280] border-t border-[#2a2a3a] pt-2">
            {result.environmental_note}
          </p>
        )}
      </div>

      <div className="cyber-card-terminal cyber-chamfer p-4 space-y-2">
        <p className="cyber-label text-[#00ff88]">&gt; Recommendation</p>
        <p className="text-sm text-[#e0e0e0]">{result.recommendation}</p>
        <p className="text-xs text-[#6b7280] italic">{result.recommendation_disclaimer}</p>
      </div>

      <Disclaimer />

      <Link
        href={`/inspection/${result.inspection_id}`}
        className="block text-center font-label text-[10px] tracking-[0.2em] uppercase text-[#00d4ff] hover:text-[#00ff88] py-2 transition-colors"
      >
        View full detail page →
      </Link>
    </div>
  );
}
