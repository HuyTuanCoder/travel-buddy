type AuthAsideProps = {
  title: string
  description: string
  bullets: string[]
}

const AuthAside = ({ title, description, bullets }: AuthAsideProps) => {
  return (
    <section className="hidden w-full max-w-sm flex-col gap-6 rounded-3xl border border-blue-100 bg-blue-50/70 p-6 text-slate-700 lg:flex">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-blue-600">
          Travel Buddy
        </p>
        <h2 className="mt-3 text-xl font-semibold text-slate-900">{title}</h2>
        <p className="mt-2 text-sm text-slate-600">{description}</p>
      </div>
      <ul className="space-y-3 text-sm text-slate-600">
        {bullets.map((bullet) => (
          <li key={bullet} className="flex items-start gap-2">
            <span className="mt-2 h-2 w-2 rounded-full bg-blue-500" />
            <span>{bullet}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default AuthAside
