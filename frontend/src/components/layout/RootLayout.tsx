import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

export default function RootLayout() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />
      <div className="flex-1 w-full flex flex-col">
        <Outlet />
      </div>
    </div>
  )
}
