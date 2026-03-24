import { useEffect, useRef } from 'react'
import { useScroll, useTransform, motion } from 'framer-motion'

const agents = [
  { title: 'KYC Verification', desc: 'Identity verification via Aadhaar OTP' },
  { title: 'Document OCR', desc: 'Extracts income & asset documents' },
  { title: 'Fraud Detection', desc: 'Multi-layer authenticity checks' },
  { title: 'Compliance Engine', desc: 'IRDAI & RBI regulatory validation' },
  { title: 'Underwriting', desc: 'Explainable AI decision model' },
  { title: 'Verification', desc: 'Sanity checks & hard-fail rules' },
  { title: 'Transparency', desc: 'Feature importance explanations' },
  { title: 'Supervision', desc: 'Final orchestration & decision' },
]

export default function AgentRailAnimation() {
  const containerRef = useRef(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start center', 'end center']
  })

  // Each agent gets its own animated path
  const pathLengths = Array.from({ length: 5 }, (_, i) => 
    useTransform(scrollYProgress, [0, (i + 1) * 0.2], [0, 1])
  )

  return (
    <div ref={containerRef} className="relative py-32 px-6 bg-[#04221f]">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="mb-20 relative z-10">
          <div className="inline-flex items-center gap-3 mb-4">
            <span className="bg-[#dbf226] text-[#04221f] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">Pipeline</span>
          </div>
          <h2 className="font-serif text-4xl md:text-5xl text-white" style={{ fontFamily: 'var(--font-serif)' }}>
            Orchestrated <span className="text-[#dbf226]">Agent Intelligence</span>
          </h2>
          <p className="text-white/60 mt-4 max-w-2xl">
            9 specialized agents work in sequence, each validating and enriching the application with defect-free precision.
          </p>
        </div>

        {/* Animated SVG Rails */}
        <div className="relative mb-16 h-96">
          <svg className="w-full h-full absolute inset-0" viewBox="0 0 800 400" preserveAspectRatio="none">
            <defs>
              <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style={{ stopColor: '#005b52', stopOpacity: 0 }} />
                <stop offset="50%" style={{ stopColor: '#dbf226', stopOpacity: 1 }} />
                <stop offset="100%" style={{ stopColor: '#005b52', stopOpacity: 0 }} />
              </linearGradient>
            </defs>

            {/* Rail 1 */}
            <motion.path
              d="M 50 80 Q 200 100, 350 80 T 750 80"
              stroke="url(#grad1)"
              strokeWidth="2"
              fill="none"
              style={{ pathLength: pathLengths[0] }}
            />

            {/* Rail 2 */}
            <motion.path
              d="M 50 150 Q 200 180, 350 150 T 750 150"
              stroke="url(#grad1)"
              strokeWidth="2"
              fill="none"
              style={{ pathLength: pathLengths[1] }}
            />

            {/* Rail 3 */}
            <motion.path
              d="M 50 220 Q 200 250, 350 220 T 750 220"
              stroke="url(#grad1)"
              strokeWidth="2"
              fill="none"
              style={{ pathLength: pathLengths[2] }}
            />

            {/* Rail 4 */}
            <motion.path
              d="M 50 290 Q 200 320, 350 290 T 750 290"
              stroke="url(#grad1)"
              strokeWidth="2"
              fill="none"
              style={{ pathLength: pathLengths[3] }}
            />

            {/* Rail 5 */}
            <motion.path
              d="M 50 360 Q 200 390, 350 360 T 750 360"
              stroke="url(#grad1)"
              strokeWidth="2"
              fill="none"
              style={{ pathLength: pathLengths[4] }}
            />
          </svg>

          {/* Station nodes */}
          <div className="absolute inset-0 flex items-center justify-between px-4">
            {['KYC', 'OCR', 'Fraud', 'Compliance', 'Underwriting'].map((name, i) => (
              <div key={i} className="flex flex-col items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-[#dbf226] border-2 border-[#04221f] flex items-center justify-center">
                  <span className="text-xs font-bold text-[#04221f]">{i + 1}</span>
                </div>
                <span className="text-xs text-white/60 mt-2 whitespace-nowrap text-center text-[10px]">{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {agents.map((agent, idx) => (
            <div
              key={idx}
              className="group p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-[#dbf226]/50 hover:bg-white/10 transition-all duration-300"
            >
              <div className="w-10 h-10 rounded-lg bg-[#005b52] text-[#dbf226] font-bold flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                {idx + 1}
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">{agent.title}</h3>
              <p className="text-xs text-white/50 leading-relaxed">{agent.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
