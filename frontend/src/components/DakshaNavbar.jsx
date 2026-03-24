import { useState, useEffect } from 'react'

export default function DakshaNavbar() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isProductsOpen, setIsProductsOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 40)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
      isScrolled 
        ? 'top-4 left-1/2 -translate-x-1/2 w-11/12 max-w-2xl' 
        : 'top-0 left-0 right-0 w-full'
    }`}>
      <div className={`px-8 py-4 flex items-center justify-between ${
        isScrolled
          ? 'bg-[#04221f]/95 backdrop-blur-xl border border-white/10 rounded-full shadow-2xl'
          : 'bg-transparent'
      }`}>
        {/* Logo */}
        <span className={`font-serif text-2xl font-bold transition-colors duration-300 ${
          isScrolled ? 'text-[#dbf226]' : 'text-[#005b52]'
        }`} style={{ fontFamily: 'var(--font-serif)' }}>
          Daksha
        </span>

        {/* Nav Links */}
        <div className={`hidden md:flex items-center gap-8 text-sm font-medium ${
          isScrolled ? 'text-white/80' : 'text-[#005b52]/70'
        }`}>
          <a href="#features" className={`hover:text-[#dbf226] transition-colors ${
            isScrolled ? 'hover:text-[#dbf226]' : 'hover:text-[#005b52]'
          }`}>
            How It Works
          </a>
          <a href="#benefits" className={`hover:text-[#dbf226] transition-colors ${
            isScrolled ? 'hover:text-[#dbf226]' : 'hover:text-[#005b52]'
          }`}>
            Why Daksha
          </a>
        </div>

        {/* CTA */}
        <button className={`px-6 py-2 rounded-full font-bold text-sm transition-all duration-300 ${
          isScrolled
            ? 'bg-[#dbf226] text-[#04221f] hover:shadow-lg'
            : 'bg-[#04221f] text-white hover:bg-[#dbf226] hover:text-[#04221f]'
        }`}>
          Start Now
        </button>
      </div>
    </nav>
  )
}
