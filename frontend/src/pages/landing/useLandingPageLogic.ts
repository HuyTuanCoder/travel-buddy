type Feature = {
  title: string
  description: string
}

type Highlight = {
  title: string
  description: string
}

type Stat = {
  label: string
  value: string
}

type LandingPageLogic = {
  features: Feature[]
  highlights: Highlight[]
  stats: Stat[]
}

export function useLandingPageLogic(): LandingPageLogic {
  const features = [
    {
      title: 'Shared trip boards',
      description: 'Align timelines, budgets, and tasks in one calm workspace.',
    },
    {
      title: 'Transparent split tracking',
      description: 'Track expenses in real time and settle without awkward math.',
    },
    {
      title: 'Tasteful recommendations',
      description: 'Capture preferences so every decision feels pre-aligned.',
    },
  ]

  const highlights = [
    {
      title: 'Mood sync',
      description: 'Lock in the vibe before booking.',
    },
    {
      title: 'Auto reminders',
      description: 'Gentle nudges keep everyone aligned.',
    },
  ]

  const stats = [
    { label: 'Avg. planning time', value: '3.2 hrs' },
    { label: 'Expenses tracked', value: '96%' },
    { label: 'Trips on track', value: '91%' },
  ]

  return { features, highlights, stats }
}
