const benefits = [
  {
    title: 'Explainable AI',
    description: 'Transparent feature contribution narratives using SHAP-style reasoning outputs.',
  },
  {
    title: 'Role-Based Access',
    description: 'Differential visibility and controls for administrators, analysts, and operators.',
  },
  {
    title: 'Real-Time Monitoring',
    description: 'Server-Sent Events keep workflows, traces, and decision stages continuously updated.',
  },
  {
    title: 'Military-Grade PII Protection',
    description: 'SHA-256 hashed compliance configuration paths and secure audit-ready handling.',
  },
]

export default function BenefitsSecurity() {
  return (
    <section className="bg-white px-6 py-24" id="resources">
      <div className="mx-auto max-w-6xl rounded-[3rem] bg-[#04221f] px-8 py-12 text-white md:px-12 md:py-16">
        <div className="relative">
          <div className="pointer-events-none absolute -right-6 -top-6 h-40 w-40 rounded-full bg-[#dbf226]/30 blur-3xl" />

          <h2 className="relative z-10 font-serif text-4xl md:text-5xl">Why Choose Daksha?</h2>
          <p className="relative z-10 mt-4 max-w-3xl text-sm leading-relaxed text-white/75 md:text-base">
            Purpose-built trust, explainability, and security controls for high-stakes forensic intelligence operations.
          </p>

          <div className="relative z-10 mt-12 grid gap-5 md:grid-cols-2">
            {benefits.map((benefit) => (
              <article key={benefit.title} className="rounded-3xl border border-white/10 bg-white/5 p-6">
                <h3 className="text-lg font-semibold text-[#dbf226]">{benefit.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-white/75">{benefit.description}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
