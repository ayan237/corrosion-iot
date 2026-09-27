/**
 * Prominent banner shown whenever inference_mode is "demo".
 * PRD sections 21 and 30 require this to be clearly displayed.
 */
export default function DemoBanner() {
  return (
    <div className="w-full cyber-chamfer border border-[#ff00ff]/50 bg-[#ff00ff]/10 text-[#ff00ff] px-4 py-3 flex items-start gap-3 text-sm neon-glow-secondary">
      <span className="text-lg leading-none mt-0.5 shrink-0" aria-hidden>
        ⚠
      </span>
      <span className="font-body tracking-wide">
        <strong className="font-heading font-bold uppercase tracking-widest">
          Demo Mode Active
        </strong>{" "}
        — AI detections are synthetically generated for testing purposes. This is{" "}
        <em>not</em> real ML inference. Add a model file and set{" "}
        <code className="bg-[#0a0a0f]/60 px-1 text-xs text-[#00d4ff]">
          MODEL_PATH
        </code>{" "}
        in <code className="bg-[#0a0a0f]/60 px-1 text-xs text-[#00d4ff]">.env</code> to
        enable real detection.
      </span>
    </div>
  );
}
