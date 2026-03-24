import { useEffect, useState } from 'react'
import { useShield } from '../context/ShieldContext'

export default function Navbar() {
  const { setView, authToken, setAuthToken, userData } = useShield()
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 40)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function clearSession() {
    setAuthToken(null)
    setView('landing')
  }

  const linkClass = `text-sm font-medium tracking-wide transition-colors duration-300 ease-out cursor-pointer ${
    isScrolled ? 'text-white/80 hover:text-[#dbf226]' : 'text-[#005b52] hover:text-[#04221f]/70'
  }`

  const btnClass = `rounded-full px-5 py-2 text-sm font-bold transition-all duration-300 ease-out ${
    isScrolled
      ? 'bg-[#dbf226] text-[#04221f] hover:bg-[#c4da1e]'
      : 'bg-[#005b52]/10 text-[#005b52] hover:bg-[#005b52] hover:text-white'
  }`

  return (
    <nav
      className={`fixed z-50 flex items-center justify-between transition-[top,width,padding,border-radius,background-color,box-shadow,transform] duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform ${
        isScrolled
          ? 'top-6 left-1/2 -translate-x-1/2 w-[95%] max-w-5xl rounded-full bg-[#04221f]/95 backdrop-blur-sm text-white shadow-2xl px-8 py-3'
          : 'top-0 left-1/2 -translate-x-1/2 w-full rounded-none bg-transparent text-[#005b52] px-10 py-6'
      }`}
    >
      <button
        onClick={() => setView('landing')}
        className={`font-serif text-3xl font-bold tracking-tight ${isScrolled ? 'text-white' : 'text-[#04221f]'}`}
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        Daksha
      </button>

      <div className="hidden md:flex items-center gap-8">
        <span className={linkClass} onClick={() => setView('how')}>How It Works</span>
        <span className={linkClass} onClick={() => setView('partner')}>Partners</span>
        <span className={linkClass} onClick={() => setView('about')}>About</span>
      </div>

      <div className="flex items-center gap-3">
        {authToken ? (
          <>
            {userData?.name && (
              <span className={`text-xs font-medium hidden sm:block truncate max-w-[120px] ${isScrolled ? 'text-white/60' : 'text-[#005b52]/60'}`}>
                {userData.name}
              </span>
            )}
            <button onClick={clearSession} className={btnClass}>Sign out</button>
          </>
        ) : (
          <button onClick={() => setView('kyc')} className={btnClass}>Get Started</button>
        )}
      </div>
    </nav>
  )
}

