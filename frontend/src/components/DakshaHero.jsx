import DakshaGlobe from './DakshaGlobe'
import { useShield } from '../context/ShieldContext'

export default function DakshaHero() {
  const { setView } = useShield()

  return (
    <section className="h-screen max-h-screen bg-[#f7faf9] relative overflow-hidden pt-28">
        {/* Background gradient blur */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 right-10 w-96 h-96 bg-[#005b52]/5 rounded-full blur-[100px]" />
          <div className="absolute bottom-20 left-10 w-96 h-96 bg-[#dbf226]/5 rounded-full blur-[100px]" />
        </div>

        <div className="absolute inset-x-0 bottom-0 z-0 pointer-events-none">
          <div className="mx-auto w-full max-w-6xl px-4 md:px-0">
            <DakshaGlobe />
          </div>
        </div>

        <div className="relative z-10 max-w-6xl mx-auto px-6 w-full h-full flex flex-col items-center justify-center text-center pb-28 md:pb-36">
          {/* Badge */}
          <div className="mb-12 px-5 py-2 rounded-full border border-black/10 bg-white/80 text-sm font-bold tracking-wide flex items-center gap-3 shadow-sm text-black">
            <span className="bg-[#dbf226] text-[#005b52] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">System Live</span>
            AI-Powered Underwriting Platform
          </div>

          {/* Headline */}
          <h1 
            className="font-serif text-8xl md:text-9xl font-bold tracking-tight mb-8 text-black leading-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Daksha
          </h1>

          {/* Subheading
          <p className="font-serif text-lg md:text-2xl text-black max-w-3xl mb-12 font-bold leading-relaxed" style={{ fontFamily: 'var(--font-serif)' }}>
            Fair, transparent loan and health insurance underwriting.
          </p> */}

          {/* CTA Button */}
          <button
            onClick={() => setView('kyc')}
            className="bg-[#04221f] text-white font-bold text-[1rem] px-9 py-4 rounded-full shadow-[0_10px_30px_rgba(4,34,31,0.3)] hover:bg-[#dbf226] hover:text-[#04221f] hover:-translate-y-1 transition-all duration-300"
          >
            Start Your Application
          </button>
        </div>
      </section>
  )
}
