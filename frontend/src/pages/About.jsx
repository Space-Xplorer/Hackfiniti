import React from 'react'
import { BrainCircuit, ShieldCheck, Scale, Sparkles } from 'lucide-react'
import GlassCard from '../components/GlassCard'

const pillars = [
  {
    title: 'Explainable Decisions',
    desc: 'Daksha uses Explainable Boosting Models so every risk decision can be traced back to interpretable feature contributions.',
    icon: <BrainCircuit className="text-[#005b52]" />,
  },
  {
    title: 'Compliance by Design',
    desc: 'The workflow enforces KYC, fraud checks, and rule-driven compliance before model output is allowed to progress.',
    icon: <Scale className="text-[#005b52]" />,
  },
  {
    title: 'User-Readable Outcomes',
    desc: 'Transparency and verification layers convert technical model behavior into clear reasons users can act on.',
    icon: <Sparkles className="text-[#005b52]" />,
  },
]

const About = () => {
  return (
    <div className="min-h-screen bg-[#f7faf9]">
      <div className="max-w-6xl mx-auto px-6 pt-36 pb-16">
        <div className="text-center mb-14">
          <span className="inline-flex items-center gap-2 text-[11px] font-bold text-[#04221f] bg-[#dbf226]/30 px-4 py-1.5 rounded-full uppercase tracking-[0.2em] mb-5">
            About Daksha
          </span>
          <h1 className="font-serif text-5xl md:text-6xl text-[#04221f] mb-4" style={{ fontFamily: 'var(--font-serif)' }}>
            Built for Trusted Underwriting
          </h1>
          <p className="text-[#005b52]/75 max-w-3xl mx-auto leading-relaxed">
            Daksha is a production-ready multi-agent underwriting system for loan and insurance decisions. It combines deterministic checks, EBM risk scoring, and explainable AI narratives in one auditable pipeline.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {pillars.map((pillar) => (
            <GlassCard key={pillar.title} className="p-7 border border-[#005b52]/10">
              <div className="w-12 h-12 rounded-2xl bg-[#005b52]/10 flex items-center justify-center mb-5">
                {pillar.icon}
              </div>
              <h3 className="text-xl font-semibold text-[#04221f] mb-2">{pillar.title}</h3>
              <p className="text-sm text-[#005b52]/70 leading-relaxed">{pillar.desc}</p>
            </GlassCard>
          ))}
        </div>

        <GlassCard className="p-8 border border-[#005b52]/10">
          <div className="flex items-start gap-3 mb-4">
            <ShieldCheck className="text-[#005b52] mt-0.5" />
            <h2 className="text-2xl font-semibold text-[#04221f]">Current System Snapshot</h2>
          </div>
          <p className="text-[#005b52]/75 mb-5 leading-relaxed">
            The live orchestration sequence includes KYC, onboarding/OCR intake, fraud analysis, feature engineering, compliance checks, underwriting inference, verification gates, transparency reasoning, and supervisor decision control.
          </p>
          <ul className="grid md:grid-cols-2 gap-3 text-sm text-[#04221f]">
            <li className="bg-[#f7faf9] rounded-xl px-4 py-3 border border-[#005b52]/10">Loan + Insurance support in one pipeline</li>
            <li className="bg-[#f7faf9] rounded-xl px-4 py-3 border border-[#005b52]/10">Event-driven agent workflow and status streaming</li>
            <li className="bg-[#f7faf9] rounded-xl px-4 py-3 border border-[#005b52]/10">EBM-based explainable scoring and feature traces</li>
            <li className="bg-[#f7faf9] rounded-xl px-4 py-3 border border-[#005b52]/10">Decision-level logging and auditability</li>
          </ul>
        </GlassCard>
      </div>
    </div>
  )
}

export default About

