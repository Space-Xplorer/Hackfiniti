import { useShield } from '../context/ShieldContext'

const agents = [
  { n: '1', title: 'KYC Verification', body: 'Instant Aadhaar identity verification via DigiLocker OTP flow.' },
  { n: '2', title: 'Document OCR', body: 'Extracts salary slips, bank statements, and ITR data with confidence scoring.' },
  { n: '3', title: 'Fraud Detection', body: 'Multi-layer CV and LLM-based document authenticity analysis.' },
  { n: '4', title: 'Compliance Engine', body: 'RAG-based regulatory validation against IRDAI and RBI rule sets.' },
  { n: '5', title: 'EBM Underwriting', body: 'Explainable Boosting Machines predict approval with full feature transparency.' },
]

const detections = [
  { icon: '📊', title: 'Income Verification', body: 'Cross-validates declared income against OCR-extracted salary slips and bank statements.' },
  { icon: '🔍', title: 'Document Authenticity', body: 'Detects tampered PDFs, metadata anomalies, and copy-paste artifacts.' },
  { icon: '⚖️', title: 'Regulatory Compliance', body: 'Validates every application against IRDAI health insurance and RBI loan guidelines.' },
]

const benefits = [
  { title: 'Explainable AI', body: 'Every decision includes feature contribution scores — you know exactly why you were approved or rejected.' },
  { title: 'OTP-Based KYC', body: 'Aadhaar OTP verification via AadhaarKYC API for secure, real identity confirmation.' },
  { title: 'Fraud-Resistant', body: 'Four-layer document fraud detection including Error Level Analysis and LLM content verification.' },
  { title: 'Sub-2-Minute Decisions', body: 'Full underwriting pipeline completes in under 2 minutes from submission to result.' },
]

export default function Landing() {
  const { setView } = useShield()

  return (
    <div className="bg-[#f7faf9] text-[#005b52]">

      {/* Hero */}
      <section className="min-h-screen flex flex-col items-center justify-center text-center px-6 pt-24 pb-16">
        <div className="mb-8 px-5 py-2 rounded-full border border-[#005b52]/10 bg-[#005b52]/5 text-sm font-semibold tracking-wide flex items-center gap-3">
          <span className="bg-[#dbf226] text-[#005b52] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">System Live</span>
          AI-Powered Underwriting Platform
        </div>
        <h1 className="font-serif text-7xl md:text-9xl font-bold tracking-tight mb-6 text-[#005b52]" style={{ fontFamily: 'var(--font-serif)' }}>
          Daksha
        </h1>
        <p className="text-lg md:text-xl text-[#005b52]/80 max-w-3xl mb-12 font-medium leading-relaxed">
          Fair, transparent loan and health insurance underwriting. Powered by explainable AI — no black boxes, no unexplained rejections.
        </p>
        <button
          onClick={() => setView('kyc')}
          className="bg-[#04221f] text-white font-bold text-lg px-8 py-4 rounded-full shadow-[0_10px_30px_rgba(4,34,31,0.3)] hover:bg-[#dbf226] hover:text-[#04221f] hover:-translate-y-1 transition-all duration-300"
        >
          Start Your Application
        </button>
      </section>

      {/* Agents */}
      <section className="bg-[#04221f] text-white py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-12">
            <span className="bg-[#dbf226] text-[#04221f] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">Architecture</span>
            <h2 className="font-serif text-4xl md:text-5xl text-[#dbf226] mt-4" style={{ fontFamily: 'var(--font-serif)' }}>Multi-Agent Intelligence</h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((a) => (
              <div key={a.n} className="p-8 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                <div className="w-12 h-12 rounded-xl bg-[#005b52] text-[#dbf226] text-2xl font-bold flex items-center justify-center mb-6">
                  {a.n}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{a.title}</h3>
                <p className="text-sm text-white/60 leading-relaxed">{a.body}</p>
              </div>
            ))}
            {/* Lime highlight card */}
            <div className="p-8 rounded-3xl bg-[#dbf226] border border-[#dbf226]/50 shadow-[0_0_30px_rgba(219,242,38,0.15)]">
              <div className="w-12 h-12 rounded-xl bg-[#04221f] text-[#dbf226] text-2xl font-bold flex items-center justify-center mb-6">✦</div>
              <h3 className="text-lg font-semibold text-[#04221f] mb-2">Transparent Decisions</h3>
              <p className="text-sm text-[#04221f]/80 leading-relaxed">Every decision comes with a plain-language explanation and feature contribution breakdown.</p>
            </div>
          </div>
        </div>
      </section>

      {/* What We Check */}
      <section className="bg-[#f7faf9] py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <h2 className="font-serif text-4xl md:text-5xl text-center text-[#005b52] mb-16" style={{ fontFamily: 'var(--font-serif)' }}>What Daksha Checks</h2>
          <div className="grid md:grid-cols-3 gap-10">
            {detections.map((d) => (
              <div key={d.title} className="text-center group">
                <div className="w-20 h-20 rounded-full mx-auto mb-6 bg-white shadow-xl flex items-center justify-center text-4xl group-hover:scale-110 group-hover:bg-[#dbf226] transition-all duration-300">
                  {d.icon}
                </div>
                <h3 className="text-xl font-semibold text-[#04221f] mb-3">{d.title}</h3>
                <p className="text-sm text-[#005b52]/70 leading-relaxed">{d.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose */}
      <section className="bg-white py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="rounded-[3rem] p-12 md:p-20 bg-[#04221f] text-white relative overflow-hidden shadow-2xl">
            <div className="pointer-events-none absolute top-0 right-0 w-96 h-96 bg-[#005b52] rounded-full blur-[120px] opacity-50 -translate-y-1/2 translate-x-1/2" />
            <h2 className="relative z-10 font-serif text-4xl md:text-5xl text-[#dbf226] mb-4" style={{ fontFamily: 'var(--font-serif)' }}>Why Choose Daksha?</h2>
            <p className="relative z-10 text-white/60 mb-12 max-w-xl">Purpose-built for fair, explainable, and fraud-resistant underwriting decisions.</p>
            <div className="relative z-10 grid md:grid-cols-2 gap-12">
              {benefits.map((b) => (
                <div key={b.title} className="flex gap-4 group">
                  <div className="w-10 h-10 shrink-0 rounded-full bg-[#dbf226]/10 text-[#dbf226] flex items-center justify-center group-hover:bg-[#dbf226] group-hover:text-[#04221f] transition-colors">
                    ✓
                  </div>
                  <div>
                    <h3 className="font-semibold text-white mb-1">{b.title}</h3>
                    <p className="text-sm text-white/60 leading-relaxed">{b.body}</p>
                  </div>
                </div>
              ))}
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

