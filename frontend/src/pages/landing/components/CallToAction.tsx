import { Link } from 'react-router-dom'

export default function CallToAction() {
  return (
    <section className="mx-auto w-full max-w-6xl px-6 pb-20">
      <div className="flex flex-col gap-6 rounded-3xl bg-slate-900 px-8 py-10 text-white shadow-lg shadow-blue-100/60 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">
            Launch your next adventure with clarity
          </h2>
          <p className="mt-2 text-sm text-slate-200">
            Invite your crew, lock the plan, and keep every traveler on the same
            page.
          </p>
        </div>
        <Link
          to="/register"
          className="inline-flex h-12 items-center justify-center rounded-lg bg-white px-8 text-sm font-semibold text-slate-900 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        >
          Get Started for Free
        </Link>
      </div>
    </section>
  )
}
