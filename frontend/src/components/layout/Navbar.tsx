import { Link, useNavigate } from 'react-router-dom'
import { Plane, LogOut, Settings, User } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function Navbar() {
  const { isAuthenticated, user, clearAuth } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = () => {
    clearAuth()
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
        {/* Left: Brand */}
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors group-hover:bg-blue-700">
              <Plane className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">
              Travel Buddy
            </span>
          </Link>

          {/* Contextual Links */}
          {isAuthenticated && (
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
              <Link to="/trips" className="hover:text-slate-900 transition-colors">
                Dashboards
              </Link>
            </nav>
          )}
        </div>

        {/* Right: Auth / Profile */}
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <div className="flex items-center gap-4">
              {/* Very simple profile actions for now, can be upgraded to a DropdownMenu later */}
              <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 border border-slate-200">
                  <User className="h-4 w-4 text-slate-500" />
                </div>
                <span className="hidden sm:inline-block">{user?.email}</span>
              </div>
              
              <div className="h-4 w-[1px] bg-slate-200 hidden sm:block"></div>
              
              <Link
                to="/profile"
                className="text-slate-500 hover:text-slate-900 transition-colors hidden sm:block"
                title="Settings"
              >
                <Settings className="h-4 w-4" />
              </Link>
              
              <button
                onClick={handleSignOut}
                className="text-slate-500 hover:text-red-600 transition-colors"
                title="Sign Out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm font-medium text-slate-600 transition-colors hover:text-slate-900"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="inline-flex h-9 items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow transition-colors hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-700"
              >
                Sign Up Free
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
