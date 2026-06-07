import { Link } from 'react-router-dom'
import AuthLayout from './components/AuthLayout'
import AuthAside from './components/AuthAside'
import AuthCard from './components/AuthCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useRegisterLogic } from './hooks/useRegisterLogic'

export default function RegisterPage() {
  const { form, error, isSubmitting, updateField, handleSubmit } =
    useRegisterLogic()

  return (
    <AuthLayout>
      <AuthAside
        title="Build your travel calm"
        description="Set up a shared workspace and start making confident, low-stress plans."
        bullets={[
          'Create a private planning studio for your crew.',
          'Collect preferences before you book.',
          'Send gentle reminders without the chaos.',
        ]}
      />
      <AuthCard
        title="Create account"
        subtitle="Start with an email and we will set up your first trip board."
      >
        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@travelbuddy.com"
              value={form.email}
              onChange={(event) => updateField('email', event.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              placeholder="Create a secure password"
              value={form.password}
              onChange={(event) => updateField('password', event.target.value)}
              required
            />
          </div>
          {error ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {error}
            </div>
          ) : null}
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </Button>
          <p className="text-sm text-slate-600">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-blue-600">
              Sign in
            </Link>
          </p>
        </form>
      </AuthCard>
    </AuthLayout>
  )
}


