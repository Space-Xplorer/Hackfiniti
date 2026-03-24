import AgentCollaboration from '../components/landing/AgentCollaboration'
import BenefitsSecurity from '../components/landing/BenefitsSecurity'
import DetectionCapabilities from '../components/landing/DetectionCapabilities'
import LandingFooter from '../components/landing/LandingFooter'
import LangGraphOrchestration from '../components/landing/LangGraphOrchestration'
import NiyatiHero from '../components/landing/NiyatiHero'

export default function Landing() {
  return (
    <main className="bg-white text-[#04221f]">
      <NiyatiHero />
      <AgentCollaboration />
      <LangGraphOrchestration />
      <DetectionCapabilities />
      <BenefitsSecurity />
      <LandingFooter />
    </main>
  )
}
