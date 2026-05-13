type SummaryCardProps = {
  label: string
  value: string
}

const SummaryCard = ({ label, value }: SummaryCardProps) => (
  <div className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-[0_12px_40px_rgba(6,11,23,0.35)]">
    <p className="text-xs uppercase tracking-[0.3em] text-white/50">{label}</p>
    <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
  </div>
)

export default SummaryCard
