import { useShield } from '../context/ShieldContext'
import DakshaHero from '../components/DakshaHero'

const agents = [
  { n: '1', title: 'KYC Verification', body: 'Instant Aadhaar identity verification via DigiLocker OTP flow.' },
  { n: '2', title: 'Onboarding Agent', body: 'Normalizes submitted profile and application payload for downstream processing.' },
  { n: '3', title: 'Fraud Detection', body: 'Multi-layer CV and LLM-based document authenticity analysis.' },
  { n: '4', title: 'Feature Engineering', body: 'Builds model-ready underwriting features from extracted and declared inputs.' },
  { n: '5', title: 'Compliance Engine', body: 'RAG-based regulatory validation against IRDAI and RBI rule sets.' },
  { n: '6', title: 'EBM Underwriting', body: 'Explainable Boosting Machines predict approval with full feature transparency.' },
  { n: '7', title: 'Verification Agent', body: 'Sanity checks and hard-fail overrides for risk thresholds.' },
  { n: '8', title: 'Transparency Agent', body: 'Generates plain-language explanations with feature breakdowns.' },
  // { n: '9', title: 'Supervisor Agent', body: 'Final orchestration and unified decision compilation.' },
]

const workflowStages = [
  {
    title: '1) Application Intake',
    body: 'User profile + submitted details are captured and normalized as structured underwriting input.',
  },
  {
    title: '2) Compliance & Document Checks',
    body: 'KYC verification, onboarding normalization, OCR-backed document checks, fraud screening, and compliance rules run in sequence.',
  },
  {
    title: '3) Risk Modeling (EBM)',
    body: 'Feature engineering feeds explainable boosting models for loan approval probability and insurance premium risk.',
  },
  {
    title: '4) AI Explanation & Final Decision',
    body: 'Verification and transparency agents produce plain-language reasoning before supervisor finalizes the outcome.',
  },
]

export default function Landing() {
  const { setView } = useShield()

  return (
    <div className="bg-[#f7faf9] text-[#005b52]">
      {/* Hero with dynamic navbar and globe */}
      <DakshaHero />

      {/* Workflow story */}
      <section className="bg-white py-20 px-6" id="features">
        <div className="max-w-7xl mx-auto">
          <div className="mb-14 text-center">
            <div className="inline-flex items-center gap-3 mb-4">
              <span className="bg-[#dbf226] text-[#04221f] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">System Workflow</span>
            </div>
            <h2 className="font-serif text-4xl md:text-5xl text-[#04221f]" style={{ fontFamily: 'var(--font-serif)' }}>
              Underwriting Flow from <span className="text-[#005b52]">Input to Explanation</span>
            </h2>
            <p className="text-[#005b52]/70 mt-3 max-w-3xl mx-auto">
              Daksha runs a deterministic agent pipeline: intake → checks (KYC, OCR, fraud, compliance) → EBM scoring → explainable AI output.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {workflowStages.map((stage) => (
              <div key={stage.title} className="p-7 rounded-3xl bg-[#f7faf9] border border-[#005b52]/10">
                <h3 className="text-lg font-semibold text-[#04221f] mb-2">{stage.title}</h3>
                <p className="text-sm text-[#005b52]/70 leading-relaxed">{stage.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Main agents */}
      <section className="bg-[#f7faf9] py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-12 text-center">
            <div className="inline-flex items-center gap-3 mb-4">
              <span className="bg-[#005b52]/10 text-[#005b52] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">Main Agents Available</span>
            </div>
            <h2 className="font-serif text-4xl md:text-5xl text-[#04221f]" style={{ fontFamily: 'var(--font-serif)' }}>
              8-Core Agent Pipeline
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {agents.map((a) => (
              <div key={a.n} className="p-8 rounded-3xl bg-[#f7faf9] border border-[#005b52]/10 hover:border-[#005b52]/30 hover:shadow-lg transition-all duration-300">
                <div className="w-12 h-12 rounded-xl bg-[#005b52] text-[#dbf226] text-2xl font-bold flex items-center justify-center mb-6">
                  {a.n}
                </div>
                <h3 className="text-lg font-semibold text-[#04221f] mb-2">{a.title}</h3>
                <p className="text-sm text-[#005b52]/70 leading-relaxed">{a.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-white py-20 px-6" id="benefits">
        <div className="max-w-7xl mx-auto">
          <div className="rounded-[3rem] p-12 md:p-20 bg-[#04221f] text-white relative overflow-hidden shadow-2xl">
            <div className="pointer-events-none absolute top-0 right-0 w-96 h-96 bg-[#005b52] rounded-full blur-[120px] opacity-50 -translate-y-1/2 translate-x-1/2" />
            <h2 className="relative z-10 font-serif text-4xl md:text-5xl text-[#dbf226] mb-4" style={{ fontFamily: 'var(--font-serif)' }}>
              Systematic. Compliant. Explainable.
            </h2>
            <p className="relative z-10 text-white/70 mb-10 max-w-2xl leading-relaxed">
              Daksha is designed for production underwriting: policy-aligned checks, EBM-driven scoring, and AI explanations that make every decision auditable.
            </p>
            <div className="relative z-10">
              <button
                onClick={() => setView('kyc')}
                className="bg-[#dbf226] text-[#04221f] font-bold px-8 py-3 rounded-full hover:bg-[#cfe41f] transition-colors"
              >
                Start Your Application
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <span className="font-serif text-2xl font-bold text-[#04221f]" style={{ fontFamily: 'var(--font-serif)' }}>Daksha</span>
          <p className="text-sm text-[#005b52]/50">© 2026 Daksha Platform. AI-Powered Underwriting. All Rights Reserved.</p>
        </div>
      </footer>
    </div>
  )
}

