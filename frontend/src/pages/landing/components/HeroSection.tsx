import { Link } from 'react-router-dom'

type Highlight = {
  title: string
  description: string
}

type Stat = {
  label: string
  value: string
}

type HeroSectionProps = {
  headline: string
  subhead: string
  highlights: Highlight[]
  stats: Stat[]
}

export default function HeroSection({
  headline,
  subhead,
  highlights,
  stats,
}: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.08),_transparent_55%)]" />
      <div className="relative mx-auto grid w-full max-w-6xl gap-12 px-6 pb-20 pt-16 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-4 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-blue-700">
            Travel Buddy Studio
          </div>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold leading-tight text-slate-900 md:text-5xl">
              {headline}
            </h1>
            <p className="text-lg text-slate-600">{subhead}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/register"
              className="inline-flex items-center justify-center rounded-full bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            >
              Start your first trip
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center justify-center rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 ring-1 ring-slate-200 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            >
              Preview the workspace
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl bg-white/80 px-4 py-3 shadow-sm ring-1 ring-slate-200"
              >
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  {stat.label}
                </p>
                <p className="text-xl font-semibold text-slate-900">
                  {stat.value}
                </p>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-6">
          <div className="relative rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm backdrop-blur">
            <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-blue-200/40 blur-3xl" />
            <div className="relative space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400">
                    Next stop
                  </p>
                  <p className="text-lg font-semibold text-slate-900">
                    Kyoto, Japan
                  </p>
                </div>
                <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                  4 travelers
                </span>
              </div>
              <div className="space-y-2 text-sm text-slate-600">
                <p>May 18 – May 26 · boutique stays + slow mornings.</p>
                <p>2 shared expenses settled, 3 reminders scheduled.</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {highlights.map((item) => (
                  <div
                    key={item.title}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
                  >
                    <p className="text-sm font-semibold text-slate-900">
                      {item.title}
                    </p>
                    <p className="text-xs text-slate-500">{item.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm backdrop-blur">
            <p className="text-xs uppercase tracking-wide text-slate-400">
              Shared planning cadence
            </p>
            <div className="mt-4 space-y-3">
              {['Choose vibe', 'Align budget', 'Finalize itinerary'].map(
                (step, index) => (
                  <div
                    key={step}
                    className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm"
                  >
                    <span className="font-semibold text-slate-900">
                      {step}
                    </span>
                    <span className="text-xs text-slate-500">
                      Step {index + 1}
                    </span>
                  </div>
                ),
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}


