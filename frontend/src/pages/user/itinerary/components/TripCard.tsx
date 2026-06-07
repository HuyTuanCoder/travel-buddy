import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { ItinerarySummaryResponse } from '@/types/itineraryTypes'

// ==================== Props ====================

interface TripCardProps {
  trip: ItinerarySummaryResponse
  onDelete: (id: string) => void
}

// ==================== Status badge color mapping ====================

const statusStyles: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-600 border-slate-200',
  ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  ARCHIVED: 'bg-amber-50 text-amber-700 border-amber-200',
}

const roleStyles: Record<string, string> = {
  OWNER: 'bg-blue-50 text-blue-700 border-blue-200',
  EDITOR: 'bg-violet-50 text-violet-700 border-violet-200',
  VIEWER: 'bg-slate-50 text-slate-500 border-slate-200',
}

// ==================== Component ====================

export default function TripCard({ trip, onDelete }: TripCardProps) {
  const navigate = useNavigate()

  // Format the creation date for display
  const formattedDate = new Date(trip.createdAt).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <Card
      className="group cursor-pointer transition-all duration-200 hover:shadow-md hover:border-slate-300"
      onClick={() => navigate(`/trips/${trip.id}`)}
    >
      <CardHeader className="flex flex-row items-start justify-between gap-4 pb-3">
        <div className="space-y-1.5 min-w-0">
          {/* Trip title — truncated if too long */}
          <h3 className="text-lg font-semibold text-slate-900 truncate">
            {trip.title}
          </h3>
          <p className="text-xs text-slate-500">{formattedDate}</p>
        </div>

        {/* Actions dropdown — stops click propagation so card doesn't navigate */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <span className="text-lg">⋯</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
            <DropdownMenuItem onClick={() => navigate(`/trips/${trip.id}`)}>
              Open
            </DropdownMenuItem>
            {trip.role === 'OWNER' && (
              <DropdownMenuItem
                className="text-red-600 focus:text-red-600"
                onClick={() => onDelete(trip.id)}
              >
                Delete
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="flex items-center gap-2">
          {/* Status badge */}
          <Badge
            variant="outline"
            className={statusStyles[trip.status] ?? ''}
          >
            {trip.status.toLowerCase()}
          </Badge>

          {/* Role badge */}
          <Badge
            variant="outline"
            className={roleStyles[trip.role] ?? ''}
          >
            {trip.role.toLowerCase()}
          </Badge>

          {/* Timezone chip */}
          <span className="ml-auto text-xs text-slate-400 hidden sm:inline">
            {trip.timezone}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}


