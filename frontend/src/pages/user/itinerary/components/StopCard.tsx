import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { TripStopResponse } from '@/types/itineraryTypes'

// ==================== Props ====================

interface StopCardProps {
  stop: TripStopResponse
  onRemove: (stopId: string) => void
}

// ==================== Stop type badge colors ====================

const stopTypeStyles: Record<string, string> = {
  ATTRACTION: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  RESTAURANT: 'bg-orange-50 text-orange-700 border-orange-200',
  LODGING: 'bg-teal-50 text-teal-700 border-teal-200',
  TRANSIT: 'bg-slate-100 text-slate-600 border-slate-200',
}

// ==================== Component ====================

export default function StopCard({ stop, onRemove }: StopCardProps) {
  // Format time for display (HH:mm → "10:30 AM")
  const formatTime = (time: string | null): string | null => {
    if (!time) return null
    const [hours, minutes] = time.split(':').map(Number)
    const ampm = hours >= 12 ? 'PM' : 'AM'
    const displayHour = hours % 12 || 12
    return `${displayHour}:${String(minutes).padStart(2, '0')} ${ampm}`
  }

  const arrival = formatTime(stop.arrivalTime)
  const departure = formatTime(stop.departureTime)

  return (
    <div className="group flex items-start gap-3 rounded-xl border border-slate-100 bg-white p-3 transition-all hover:border-slate-200 hover:shadow-sm">
      {/* Visit order indicator */}
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
        {stop.visitOrder}
      </div>

      {/* Stop details */}
      <div className="flex-1 min-w-0 space-y-1.5">
        {/* Place ID and type badge */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-800 truncate">
            {stop.googlePlaceId}
          </span>
          <Badge
            variant="outline"
            className={`text-[10px] ${stopTypeStyles[stop.stopType] ?? ''}`}
          >
            {stop.stopType.toLowerCase()}
          </Badge>
        </div>

        {/* Time range and cost */}
        <div className="flex items-center gap-3 text-xs text-slate-500">
          {(arrival || departure) && (
            <span>
              {arrival ?? '—'} → {departure ?? '—'}
            </span>
          )}
          {stop.estimatedCost != null && (
            <span className="text-emerald-600 font-medium">
              ${Number(stop.estimatedCost).toFixed(2)}
            </span>
          )}
        </div>

        {/* User notes */}
        {stop.userNotes && (
          <p className="text-xs text-slate-400 italic truncate">
            {stop.userNotes}
          </p>
        )}
      </div>

      {/* Remove button — visible on hover */}
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-600"
        onClick={() => onRemove(stop.id)}
      >
        ✕
      </Button>
    </div>
  )
}


