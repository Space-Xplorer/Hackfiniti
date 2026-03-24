import React from 'react'
import { useShield } from '../context/ShieldContext'
import { Building2, ShieldCheck, Workflow, FileText, ArrowRight } from 'lucide-react'
import GlassCard from '../components/GlassCard'

const partnerFits = [
  {
    title: 'Digital Lending Teams',
    desc: 'Automate intake, document checks, and explainable credit decisions for operational underwriting flows.',
  },
  {
    title: 'Insurance Operations',
    desc: 'Run policy checks and risk modeling with transparent premium and recommendation reasoning.',
  },
  {
    title: 'Risk & Compliance Units',
    desc: 'Use deterministic logs and stage-level outputs for internal review and governance workflows.',
  },
]

const Partners = () => {
  const { setView } = useShield()

  return (
    <div className="min-h-screen bg-[#f7faf9]">
      <div className="max-w-7xl mx-auto px-6 pt-36 pb-16">
        <div className="grid lg:grid-cols-2 gap-8 items-start mb-12">
          <div>
            <span className="inline-flex items-center gap-2 text-[11px] font-bold text-[#04221f] bg-[#dbf226]/30 px-4 py-1.5 rounded-full uppercase tracking-[0.2em] mb-5">
              Partners
            </span>
            <h1 className="font-serif text-5xl md:text-6xl text-[#04221f] mb-4" style={{ fontFamily: 'var(--font-serif)' }}>
              Integrate Daksha in Existing Workflows
            </h1>
            <p className="text-[#005b52]/75 leading-relaxed max-w-xl mb-6">
              Daksha is suited for organizations that need a practical underwriting pipeline with compliance controls, explainable model outputs, and clear audit trails.
            </p>
            <button
              onClick={() => setView('kyc')}
              className="bg-[#04221f] text-white font-bold px-7 py-3 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] transition-colors"
            >
              Start Pilot Flow
            </button>
          </div>

          <GlassCard className="p-7 border border-[#005b52]/10">
            <h2 className="text-xl font-semibold text-[#04221f] mb-4">Current Platform Capabilities</h2>
            <ul className="space-y-3 text-sm text-[#005b52]/75">
              <li className="flex items-start gap-3"><Workflow className="text-[#005b52] mt-0.5" size={16} /> Sequential multi-agent orchestration with status progression</li>
              <li className="flex items-start gap-3"><FileText className="text-[#005b52] mt-0.5" size={16} /> OCR-assisted document processing and normalized field extraction</li>
              <li className="flex items-start gap-3"><ShieldCheck className="text-[#005b52] mt-0.5" size={16} /> Rule-based compliance + verification before final recommendation</li>
              <li className="flex items-start gap-3"><Building2 className="text-[#005b52] mt-0.5" size={16} /> Loan and insurance decision support in one application stack</li>
            </ul>
          </GlassCard>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {partnerFits.map((item) => (
            <GlassCard key={item.title} className="p-7 border border-[#005b52]/10">
              <h3 className="text-lg font-semibold text-[#04221f] mb-2">{item.title}</h3>
              <p className="text-sm text-[#005b52]/70 leading-relaxed">{item.desc}</p>
            </GlassCard>
          ))}
        </div>

        <GlassCard className="p-8 border border-[#005b52]/10 text-center">
          <h2 className="text-2xl font-semibold text-[#04221f] mb-3">Need a System Walkthrough?</h2>
          <p className="text-[#005b52]/75 max-w-2xl mx-auto mb-6">
            We can map your existing intake and underwriting process to the Daksha agent pipeline and define the integration steps.
          </p>
          <button className="inline-flex items-center gap-2 bg-[#04221f] text-white font-semibold px-6 py-3 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] transition-colors">
            Request Integration Brief <ArrowRight size={16} />
          </button>
        </GlassCard>
      </div>
    </div>
  )
}

export default Partners

