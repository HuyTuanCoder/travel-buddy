import type { ReactNode } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

type AuthCardProps = {
  title: string
  subtitle: string
  children: ReactNode
}

export default function AuthCard({ title, subtitle, children }: AuthCardProps) {
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        <p className="text-sm text-slate-600">{subtitle}</p>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}


