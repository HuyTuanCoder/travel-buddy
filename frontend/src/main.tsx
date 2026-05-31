import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'

// Pages
import LandingPage from '@/pages/landing/LandingPage.tsx'
import LoginPage from '@/pages/auth/LoginPage.tsx'
import RegisterPage from '@/pages/auth/RegisterPage.tsx'
import UserProfilePage from '@/pages/user/profile/UserProfilePage'

// Route Protection Setup
import ProtectedRoute from '@/components/ProtectedRoute.tsx'
import { AuthProvider } from '@/contexts/AuthContext.tsx'

const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: '/profile',
        element: <UserProfilePage />,
      },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </StrictMode>,
)
