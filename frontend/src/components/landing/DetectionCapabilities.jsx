const detections = [
  {
    icon: '🔄',
    title: 'Circular Trading',
    text: 'Identifies complex, multi-hop transaction loops designed to fabricate turnover and ITC legitimacy.',
  },
  {
    icon: '👻',
    title: 'Ghost Invoices',
    text: 'Isolates high-value GSTR-1 invoices lacking corresponding E-Way Bill evidence or movement trails.',
  },
  {
    icon: '🕸️',
    title: 'Spider Web Networks',
    text: 'Discovers hidden shell-company clusters with orchestrated ownership and transaction camouflage.',
  },
]

export default function DetectionCapabilities() {
  return (
    <section className="bg-[#f7faf9] px-6 py-24" id="industries">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center font-serif text-4xl text-[#04221f] md:text-5xl">What We Detect</h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-sm leading-relaxed text-[#113a35]/80 md:text-base">
          Multi-agent reasoning pinpoints high-impact GST fraud patterns before they spread through the ecosystem.
        </p>

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {detections.map((detection) => (
            <article key={detection.title} className="rounded-3xl bg-white p-7 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-xl">
              <div className="grid h-20 w-20 place-items-center rounded-full bg-white text-4xl shadow-lg transition duration-200 hover:scale-110">
                {detection.icon}
              </div>
              <h3 className="mt-6 text-xl font-semibold text-[#04221f]">{detection.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[#113a35]/75">{detection.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
