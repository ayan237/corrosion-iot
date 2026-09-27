interface Props {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}

export default function StatCard({
  label,
  value,
  sub,
  accent = "neon-text",
}: Props) {
  return (
    <div className="cyber-card cyber-chamfer cyber-card-hover p-4 flex flex-col gap-1.5">
      <p className="cyber-label">{label}</p>
      <p className={`text-2xl font-heading font-bold tracking-wider ${accent}`}>
        {value}
      </p>
      {sub && <p className="text-[10px] font-label tracking-widest text-[#6b7280] uppercase">{sub}</p>}
    </div>
  );
}
