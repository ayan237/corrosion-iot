import { severityBadgeBg } from "@/lib/utils";

interface Props {
  level: string | null;
  size?: "sm" | "md" | "lg";
}

export default function SeverityBadge({ level, size = "md" }: Props) {
  const sizeClass = {
    sm: "text-[10px] px-2 py-0.5",
    md: "text-xs px-2.5 py-1",
    lg: "text-sm px-3 py-1.5 font-semibold",
  }[size];

  return (
    <span
      className={`inline-block font-label uppercase tracking-[0.15em] cyber-chamfer-sm ${sizeClass} ${severityBadgeBg(level)}`}
    >
      {level ?? "—"}
    </span>
  );
}
