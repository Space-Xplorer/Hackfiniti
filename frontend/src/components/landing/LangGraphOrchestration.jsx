const orchestrationCards = [
  { title: 'Ingestion Wrangler', icon: '📥', text: 'Ingests and normalizes GST records, filings, and transactional evidence.' },
  { title: 'Graph Architect', icon: '🕸️', text: 'Builds relation-first intelligence maps connecting entities, invoices, and risk hops.' },
  { title: 'Risk Detective', icon: '🔍', text: 'Scores anomaly vectors across compliance, timing, and behavioral signatures.' },
  { title: 'Predictive Analyst', icon: '📊', text: 'Prioritizes intervention paths with interpretable forecasting and severity signals.' },
  { title: 'Niyati Explainer', icon: '💡', text: 'Generates traceable reasoning for each recommendation and decision branch.' },
  { title: 'Seamless Sync', icon: '🔗', text: 'LangGraph orchestration keeps all agents synchronized for reliable, real-time outcomes.' },
]

export default function LangGraphOrchestration() {
  return (
    <section className="bg-[#04221f] px-6 py-24 text-white">
      <div className="mx-auto max-w-6xl">
        <h2 className="font-serif text-4xl text-[#dbf226] md:text-5xl">LangGraph Orchestration</h2>
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-white/75 md:text-base">
          A structured agent choreography layer that coordinates every analysis phase from ingestion to explainability.
        </p>

        <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {orchestrationCards.map((card) => (
            <article key={card.title} className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[#005b52] text-xl text-[#dbf226]">
                {card.icon}
              </div>
              <h3 className="mt-4 text-lg font-semibold text-[#dbf226]">{card.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/75">{card.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
