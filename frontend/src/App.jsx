import { ShieldProvider, useShield } from './context/ShieldContext'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import KYC from './pages/KYC'
import Selection from './pages/Selection'
import Upload from './pages/Upload'
import Analysis from './pages/Analysis'
import Result from './pages/Result'
import Config from './pages/Config'
import Preliminary from './pages/Preliminary'
import Partners from './pages/Partners'
import About from './pages/About'
import HowItWorks from './pages/HowItWorks'

function NavigationSource() {
  const { view } = useShield()
  switch (view) {
    case 'landing':    return <Landing />
    case 'kyc':        return <KYC />
    case 'selection':  return <Selection />
    case 'prelim':     return <Preliminary />
    case 'upload':     return <Upload />
    case 'analysis':   return <Analysis />
    case 'result':     return <Result />
    case 'config':     return <Config />
    case 'partner':    return <Partners />
    case 'about':      return <About />
    case 'how':        return <HowItWorks />
    default:           return <Landing />
  }
}

function AppShell() {
  const { view } = useShield()
  const fixedScrollViews = new Set(['landing', 'partner', 'about', 'how', 'result', 'analysis'])

  return (
    <div className="min-h-screen bg-[#FAF9F6]">
      <Navbar />
      <main className={fixedScrollViews.has(view) ? '' : 'pt-20'}>
        <NavigationSource />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ShieldProvider>
      <AppShell />
    </ShieldProvider>
  )
}
