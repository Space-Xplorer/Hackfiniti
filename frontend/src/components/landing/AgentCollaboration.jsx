import { motion, useScroll, useTransform } from 'framer-motion'
import { useRef } from 'react'

const agents = [
  { name: 'Ingestion Wrangler', icon: '📥', detail: 'Normalizes filings, invoices, and compliance payloads into graph-ready signals.' },
  { name: 'Risk Detective', icon: '🔍', detail: 'Finds fraud probability spikes, anomaly segments, and risky trade behavior.' },
  { name: 'Predictive Analyst', icon: '📊', detail: 'Forecasts exposure and prioritizes cases using interpretable risk scoring.' },
  { name: 'Niyati Explainer', icon: '💡', detail: 'Turns model outputs into transparent, audit-friendly rationale and evidence trails.' },
  { name: 'Graph Architect', icon: '🕸️', detail: 'Builds dynamic taxpayer-entity networks and relation-aware investigation maps.' },
  { name: 'Shadow Mirror', icon: '🔮', detail: 'Simulates adversarial scenarios to expose hidden vulnerabilities before exploitation.' },
]

export default function AgentCollaboration() {
  const containerRef = useRef(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start 75%', 'end 35%'],
  })

  const lineProgress = useTransform(scrollYProgress, [0, 1], [0, 1])

  return (
    <section ref={containerRef} className="relative bg-white px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center font-serif text-4xl text-[#04221f] md:text-5xl">The 6-Agent Force</h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-sm leading-relaxed text-[#113a35]/80 md:text-base">
          Scroll-activated collaboration paths show how every agent contributes to a cohesive forensic intelligence flow.
        </p>

        <div className="relative mt-16">
          <svg className="pointer-events-none absolute inset-0 hidden h-full w-full md:block" viewBox="0 0 1200 480" preserveAspectRatio="none">
            <motion.path
              d="M120 120 C 260 40, 420 40, 560 120"
              stroke="#005b52"
              strokeWidth="2.5"
              fill="none"
              style={{ pathLength: lineProgress }}
            />
            <motion.path
              d="M560 120 C 690 200, 860 200, 1040 120"
              stroke="#005b52"
              strokeWidth="2.5"
              fill="none"
              style={{ pathLength: lineProgress }}
            />
            <motion.path
              d="M300 320 C 500 260, 700 260, 900 320"
              stroke="#dbf226"
              strokeWidth="2.5"
              fill="none"
              style={{ pathLength: lineProgress }}
            />
          </svg>

          <div className="grid gap-6 md:grid-cols-3">
            {agents.map((agent) => (
              <article key={agent.name} className="relative rounded-3xl border border-[#113a35]/10 bg-[#f7faf9] p-6 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-lg">
                <div className="text-3xl">{agent.icon}</div>
                <h3 className="mt-4 text-lg font-semibold text-[#04221f]">{agent.name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#113a35]/75">{agent.detail}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
