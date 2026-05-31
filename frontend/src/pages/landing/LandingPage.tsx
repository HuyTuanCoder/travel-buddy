import { useLandingPageLogic } from './useLandingPageLogic'
import HeroSection from './components/HeroSection'
import FeatureGrid from './components/FeatureGrid'
import CallToAction from './components/CallToAction'

const LandingPage = () => {
  const { features, highlights, stats } = useLandingPageLogic()

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <HeroSection
        headline="Design a calmer way to plan travel."
        subhead="Bring budgets, itineraries, and shared decisions into one gentle workspace built for real trips."
        highlights={highlights}
        stats={stats}
      />
      <FeatureGrid features={features} />
      <CallToAction />
    </main>
  )
}

export default LandingPage
