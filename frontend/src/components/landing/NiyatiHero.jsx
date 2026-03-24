import { useEffect, useState } from 'react'
import AsciiGlobeCanvas from './AsciiGlobeCanvas'

const productItems = [
  {
    name: 'Ghost Signal',
    description: 'Isolate suspicious invoice patterns and silent compliance anomalies.',
  },
  {
    name: 'Spider Web Engine',
    description: 'Reveal shell-company clusters and hidden trade-network dependencies.',
  },
  {
    name: 'Payment Gap',
    description: 'Track ITC and filing mismatches with real-time transaction intelligence.',
  },
  {
    name: 'Explainable AI',
    description: 'Generate transparent risk narratives and feature-level explanations.',
  },
]

export default function NiyatiHero() {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => {
      setIsScrolled(window.scrollY > 40)
    }

    onScroll()
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <section className="relative overflow-hidden bg-white pb-20 text-[#04221f]">
      <div className="pointer-events-none absolute inset-0 opacity-75">
        <AsciiGlobeCanvas isBackground />
      </div>

      <div className="pointer-events-none absolute inset-0 bg-white/65" />

      <nav
        className={`fixed left-1/2 top-5 z-50 w-[94%] max-w-6xl -translate-x-1/2 transition-all duration-300 ${
          isScrolled
            ? 'rounded-full bg-[#04221f]/95 px-6 py-3 shadow-xl shadow-black/25 backdrop-blur-md'
            : 'rounded-full border border-[#04221f]/10 bg-white/90 px-6 py-3 shadow-md shadow-[#04221f]/10 backdrop-blur-md'
        }`}
      >
        <div className="flex items-center justify-between gap-6">
          <div className={`font-serif text-2xl tracking-wide ${isScrolled ? 'text-white' : 'text-[#04221f]'}`}>Daksha</div>

          <div className={`hidden items-center gap-8 text-sm md:flex ${isScrolled ? 'text-white/90' : 'text-[#04221f]/90'}`}>
            <a href="#industries" className="transition hover:text-[#005b52]">Industries</a>
            <a href="#resources" className="transition hover:text-[#005b52]">Resources</a>

            <div className="group relative">
              <button className="flex items-center gap-2 transition hover:text-[#005b52]">
                Products
                <span className="text-xs">▾</span>
              </button>

              <div className="invisible absolute left-1/2 top-[calc(100%+1rem)] w-[720px] -translate-x-1/2 scale-95 rounded-3xl border border-white/10 bg-[#04221f]/95 p-6 opacity-0 shadow-2xl transition duration-200 group-hover:visible group-hover:scale-100 group-hover:opacity-100">
                <div className="grid grid-cols-2 gap-4">
                  {productItems.map((item) => (
                    <article key={item.name} className="rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:border-[#dbf226]/40 hover:bg-white/10">
                      <h3 className="text-sm font-semibold text-[#dbf226]">{item.name}</h3>
                      <p className="mt-2 text-xs leading-relaxed text-white/75">{item.description}</p>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              className={`hidden rounded-full px-4 py-2 text-sm transition sm:inline-flex ${
                isScrolled
                  ? 'border border-white/20 text-white hover:border-[#dbf226] hover:text-[#dbf226]'
                  : 'border border-[#04221f]/20 text-[#04221f] hover:border-[#005b52] hover:text-[#005b52]'
              }`}
            >
              Log In
            </button>
            <button className="rounded-full bg-[#dbf226] px-4 py-2 text-sm font-semibold text-[#04221f] transition hover:-translate-y-0.5 hover:bg-[#eef98a]">
              Contact Us
            </button>
            <button
              aria-label="Quick action"
              className={`grid h-10 w-10 place-items-center rounded-full text-sm transition ${
                isScrolled
                  ? 'border border-white/20 bg-white/5 text-white hover:border-[#dbf226] hover:text-[#dbf226]'
                  : 'border border-[#04221f]/15 bg-white/60 text-[#04221f] hover:border-[#005b52] hover:text-[#005b52]'
              }`}
            >
              ⌁
            </button>
          </div>
        </div>
      </nav>

      <div className="relative z-10 mx-auto max-w-6xl px-6 pt-36">
        <div>
          {/* <div className="inline-flex items-center rounded-full border border-[#005b52]/20 bg-white/80 px-4 py-2 text-xs uppercase tracking-[0.15em] text-[#005b52] shadow-sm">
            System Live | Forensic Multi-Agent Intelligence Layer
          </div> */}

          <h1 className="mt-8 font-serif text-6xl leading-none sm:text-7xl md:text-8xl">Daksha</h1>

          <p className="mt-6 max-w-2xl text-base leading-relaxed text-[#113a35]/85 sm:text-lg">
            Real-time GST Intelligence Platform. Detect circular trading loops, isolate payment gaps, discover hidden network risks,
            and explain every decision with transparent multi-agent evidence.
          </p>

          <button className="mt-8 rounded-full bg-[#dbf226] px-7 py-3 text-sm font-semibold text-[#04221f] shadow-lg shadow-[#dbf226]/30 transition duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-[#dbf226]/40">
            Run Pre-Audit Safety Check
          </button>
        </div>
      </div>
    </section>
  )
}
