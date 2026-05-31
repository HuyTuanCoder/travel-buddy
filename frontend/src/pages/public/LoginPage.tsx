import { Link } from 'react-router-dom'
import AuthLayout from './components/AuthLayout'
import AuthAside from './components/AuthAside'
import AuthCard from './components/AuthCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLoginLogic } from './hooks/useLoginLogic'

const LoginPage = () => {
  const { form, error, isSubmitting, updateField, handleSubmit } =
    useLoginLogic()

  return (
    <AuthLayout>
      <AuthAside
        title="Welcome back"
        description="Keep your trip plan serene and your crew aligned from one calm dashboard."
        bullets={[
          'Revisit shared itineraries in seconds.',
          'Track who confirmed what, effortlessly.',
          'Keep decisions synced across the crew.',
        ]}
      />
      <AuthCard
        title="Sign in"
        subtitle="Use your email to continue planning your next escape."
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
              autoComplete="current-password"
              placeholder="••••••••"
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
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </Button>
          <p className="text-sm text-slate-600">
            New here?{' '}
            <Link to="/register" className="font-semibold text-blue-600">
              Create an account
            </Link>
          </p>
        </form>
      </AuthCard>
    </AuthLayout>
  )
}

export default LoginPage
