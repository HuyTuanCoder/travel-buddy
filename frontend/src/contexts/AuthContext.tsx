import React, { createContext, useContext, useState } from 'react'

type AuthUser = {
  email: string
}

type AuthContextValue = {
  isAuthenticated: boolean
  user: AuthUser | null
  accessToken: string | null
  setAuth: (token: string, user: AuthUser) => void
  clearAuth: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState(
    localStorage.getItem('access_token'),
  )
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem('auth_user')
    return raw ? (JSON.parse(raw) as AuthUser) : null
  })
  const isAuthenticated = Boolean(accessToken)

  const setAuth = (token: string, nextUser: AuthUser) => {
    localStorage.setItem('access_token', token)
    localStorage.setItem('auth_user', JSON.stringify(nextUser))
    setAccessToken(token)
    setUser(nextUser)
  }

  const clearAuth = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('auth_user')
    setAccessToken(null)
    setUser(null)
  }

  const value = {
    isAuthenticated,
    user,
    accessToken,
    setAuth,
    clearAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
