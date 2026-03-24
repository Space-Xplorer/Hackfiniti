export default function FeatureChart({ contributions = {} }) {
  const rows = Object.entries(contributions).slice(0, 5);
  return (
    <section className="bg-white/70 border border-white rounded-3xl p-5">
      <h4 className="text-xs font-black uppercase tracking-widest text-[#4B0082] mb-4">Feature Contributions</h4>
      <div className="space-y-3">
        {rows.length === 0 ? (
          <p className="text-xs text-slate-400">No contribution data.</p>
        ) : (
          rows.map(([name, value]) => (
            <div key={name}>
              <div className="flex justify-between text-[10px] font-bold text-slate-500 mb-1">
                <span>{name}</span>
                <span>{Number(value).toFixed(2)}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full bg-[#4B0082]" style={{ width: `${Math.min(Math.abs(Number(value)) * 100, 100)}%` }} />
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
