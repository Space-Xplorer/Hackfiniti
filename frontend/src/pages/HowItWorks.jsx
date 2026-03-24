import React from 'react'
import { ArrowRight, ShieldCheck, BrainCircuit, MessageSquareQuote } from 'lucide-react'
import GlassCard from '../components/GlassCard'

const stages = [
  {
    step: '01',
    title: 'Intake + KYC',
    desc: 'Application data is submitted and KYC identity checks are executed before downstream risk processing.',
  },
  {
    step: '02',
    title: 'Onboarding + OCR + Fraud',
    desc: 'Documents are extracted, normalized, and screened for inconsistencies or fraud indicators.',
  },
  {
    step: '03',
    title: 'Compliance + Feature Engineering',
    desc: 'Regulatory rule checks and feature generation prepare structured inputs for underwriting models.',
  },
  {
    step: '04',
    title: 'EBM + Verification + Transparency',
    desc: 'Explainable model output is validated through hard checks and translated into user-readable reasons.',
  },
  {
    step: '05',
    title: 'Supervisor Finalization',
    desc: 'All agent outputs are merged into final status, recommendation, and explanatory trace.',
  },
]

const HowItWorks = () => {
  return (
    <div className="min-h-screen bg-[#f7faf9]">
      <div className="max-w-7xl mx-auto px-6 pt-36 pb-16">
        <div className="text-center mb-14">
          <span className="inline-flex items-center gap-2 text-[11px] font-bold text-[#04221f] bg-[#dbf226]/30 px-4 py-1.5 rounded-full uppercase tracking-[0.2em] mb-5">
            How It Works
          </span>
          <h1 className="font-serif text-5xl md:text-6xl text-[#04221f] mb-4" style={{ fontFamily: 'var(--font-serif)' }}>
            Deterministic Agent Workflow
          </h1>
          <p className="text-[#005b52]/75 max-w-3xl mx-auto leading-relaxed">
            Daksha is a sequential orchestration system, not a single black-box model. Each stage has strict responsibilities and handoff contracts.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-4 mb-12">
          {stages.map((stage, index) => (
            <GlassCard key={stage.step} className="p-6 border border-[#005b52]/10">
              <div className="text-[11px] font-bold text-[#005b52] mb-2">Phase {stage.step}</div>
              <h3 className="text-base font-semibold text-[#04221f] mb-2">{stage.title}</h3>
              <p className="text-sm text-[#005b52]/70 leading-relaxed">{stage.desc}</p>
              {index < stages.length - 1 && <ArrowRight className="mt-4 text-[#005b52]/40" size={16} />}
            </GlassCard>
          ))}
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <GlassCard className="p-7 border border-[#005b52]/10">
            <BrainCircuit className="text-[#005b52] mb-4" />
            <h3 className="text-lg font-semibold text-[#04221f] mb-2">Explainable EBM Core</h3>
            <p className="text-sm text-[#005b52]/70 leading-relaxed">
              Underwriting uses explainable boosting models so contribution-level reasoning is retained and available for audits.
            </p>
          </GlassCard>

          <GlassCard className="p-7 border border-[#005b52]/10">
            <ShieldCheck className="text-[#005b52] mb-4" />
            <h3 className="text-lg font-semibold text-[#04221f] mb-2">Verification Layer</h3>
            <p className="text-sm text-[#005b52]/70 leading-relaxed">
              Hard fail constraints and consistency checks run after model output to ensure operational reliability and policy safety.
            </p>
          </GlassCard>

          <GlassCard className="p-7 border border-[#005b52]/10">
            <MessageSquareQuote className="text-[#005b52] mb-4" />
            <h3 className="text-lg font-semibold text-[#04221f] mb-2">Transparency Output</h3>
            <p className="text-sm text-[#005b52]/70 leading-relaxed">
              The final explanation summarizes key factors and decisions in plain language for users, operators, and reviewers.
            </p>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}

export default HowItWorks

