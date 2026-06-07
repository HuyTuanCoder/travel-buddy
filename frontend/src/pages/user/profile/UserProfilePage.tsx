import { useProfilePageLogic } from './useProfilePageLogic'
import ProfileOverview from './components/ProfileOverview'

export default function UserProfilePage() {
  useProfilePageLogic()

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto w-full max-w-4xl px-6 py-16">
        <ProfileOverview />
      </div>
    </main>
  )
}


