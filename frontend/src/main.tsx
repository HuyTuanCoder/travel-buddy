import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'

// Pages
import LandingPage from '@/pages/landing/LandingPage.tsx'
import LoginPage from '@/pages/auth/LoginPage.tsx'
import RegisterPage from '@/pages/auth/RegisterPage.tsx'
import UserProfilePage from '@/pages/user/profile/UserProfilePage'
import ItineraryListPage from '@/pages/user/itinerary/ItineraryListPage'
import ItineraryDetailPage from '@/pages/user/itinerary/ItineraryDetailPage'

// Route Protection Setup
import ProtectedRoute from '@/components/ProtectedRoute.tsx'
import { AuthProvider } from '@/contexts/AuthContext.tsx'
import RootLayout from '@/components/layout/RootLayout.tsx'

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    element: <RootLayout />,
    children: [
      {
        path: '/',
        element: <LandingPage />,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: '/profile',
            element: <UserProfilePage />,
          },
          {
            path: '/trips',
            element: <ItineraryListPage />,
          },
          {
            path: '/trips/:id',
            element: <ItineraryDetailPage />,
          },
        ],
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
