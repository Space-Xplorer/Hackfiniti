export default function AgentStatus({ name, description, status }) {
  const isPending  = status === 'pending'  || status === 'waiting'
  const isRunning  = status === 'running'  || status === 'loading'
  const isComplete = status === 'complete'

  const containerClass = isPending
    ? 'flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/10 opacity-40 transition-all duration-500'
    : isRunning
    ? 'flex items-center gap-4 p-4 rounded-2xl bg-[#dbf226]/10 border border-[#dbf226]/30 ring-1 ring-[#dbf226]/20 transition-all duration-500'
    : 'flex items-center gap-4 p-4 rounded-2xl bg-[#005b52]/20 border border-[#005b52]/30 transition-all duration-500'

  return (
    <div className={containerClass}>
      <div className="shrink-0 w-5 h-5 flex items-center justify-center">
        {isPending && <div className="w-5 h-5 rounded-full bg-white/20" />}
        {isRunning && (
          <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="#dbf226" strokeWidth="3" />
            <path className="opacity-75" fill="#dbf226" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
        )}
        {isComplete && (
          <div className="w-5 h-5 rounded-full bg-[#005b52] flex items-center justify-center">
            <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none">
              <path d="M2 6l3 3 5-5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        )}
      </div>
      <div className="min-w-0">
        <p className={`text-sm font-semibold ${isPending ? 'text-white/40' : 'text-white'}`}>{name}</p>
        {description && <p className="text-xs text-white/50 mt-0.5 truncate">{description}</p>}
      </div>
    </div>
  )
}
