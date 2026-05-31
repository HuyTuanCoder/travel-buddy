type Feature = {
  title: string
  description: string
}

type FeatureGridProps = {
  features: Feature[]
}

const FeatureGrid = ({ features }: FeatureGridProps) => {
  return (
    <section className="mx-auto w-full max-w-6xl px-6 py-16">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Calm planning system
          </p>
          <h2 className="text-2xl font-semibold text-slate-900">
            Everything your crew needs
          </h2>
        </div>
        <p className="max-w-md text-sm text-slate-600">
          Bring planning, payments, and accountability together without the
          spreadsheet chaos.
        </p>
      </div>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => (
          <article
            key={feature.title}
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h3 className="text-base font-semibold text-slate-900">
              {feature.title}
            </h3>
            <p className="mt-2 text-sm text-slate-600">
              {feature.description}
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}

export default FeatureGrid
