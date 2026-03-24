export default function GlassCard({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-3xl border border-[#005b52]/10 shadow-xl shadow-black/5 ${className}`}>
      {children}
    </div>
  )
}
