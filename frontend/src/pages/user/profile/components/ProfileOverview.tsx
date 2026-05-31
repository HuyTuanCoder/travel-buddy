import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

const ProfileOverview = () => {
  const { user, accessToken, clearAuth } = useAuth()

  return (
    <section>
      <Card className="mx-auto max-w-2xl">
        <CardHeader>
          <p className="text-xs uppercase tracking-[0.2em] text-blue-600">
            Authorization check
          </p>
          <h1 className="text-2xl font-semibold text-slate-900">
            You are signed in
          </h1>
          <p className="text-sm text-slate-600">
            This page only confirms the auth flow is wired correctly.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-slate-400">
              Signed in as
            </p>
            <p className="text-sm font-semibold text-slate-900">
              {user?.email ?? 'Unknown'}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-slate-400">
              Access token stored
            </p>
            <p className="text-sm font-semibold text-slate-900">
              {accessToken ? 'Yes' : 'No'}
            </p>
          </div>
          <Button variant="secondary" type="button" onClick={clearAuth}>
            Sign out
          </Button>
        </CardContent>
      </Card>
    </section>
  )
}

export default ProfileOverview
