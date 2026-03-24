export default function AgentTracePanel({ events = [] }) {
  return (
    <section className="bg-white/70 border border-white rounded-3xl p-5">
      <h4 className="text-xs font-black uppercase tracking-widest text-[#4B0082] mb-4">Agent Trace</h4>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-xs text-slate-400">No stream events yet.</p>
        ) : (
          events.map((event, idx) => (
            <div key={idx} className="text-xs text-slate-600 font-mono">
              {JSON.stringify(event)}
            </div>
          ))
        )}
      </div>
    </section>
  );
}
