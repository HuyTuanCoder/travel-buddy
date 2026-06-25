import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import { Draggable } from '@hello-pangea/dnd'
import { GripVertical, Pencil, Trash2, Sparkles } from 'lucide-react'
import type { TripStopResponse, UpdateStopRequest } from '@/types/itineraryTypes'
import EditStopDialog from './EditStopDialog'

// ==================== Props ====================

interface StopCardProps {
  stop: TripStopResponse
  index: number
  onUpdate: (stopId: string, payload: UpdateStopRequest) => void
  onRemove: (stopId: string) => void
  isDraft?: boolean
  isAiModified?: boolean
}

// ==================== Stop type badge colors ====================

const stopTypeStyles: Record<string, string> = {
  ATTRACTION: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  RESTAURANT: 'bg-orange-50 text-orange-700 border-orange-200',
  LODGING: 'bg-teal-50 text-teal-700 border-teal-200',
  TRANSIT: 'bg-slate-100 text-slate-600 border-slate-200',
}

// ==================== Component ====================

export default function StopCard({ stop, index, onUpdate, onRemove, isDraft, isAiModified }: StopCardProps) {
  const [isEditOpen, setIsEditOpen] = useState(false)
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
    <Draggable draggableId={stop.id} index={index}>
      {(provided: any) => (
        <>
          <div
            ref={provided.innerRef}
            {...provided.draggableProps}
            className={`group relative flex items-start gap-3 rounded-xl border p-3 transition-all ${
              isDraft
                ? 'border-dashed border-blue-400 bg-blue-50/50 hover:bg-blue-50'
                : 'border-slate-100 bg-white hover:border-slate-200 hover:shadow-sm'
            } ${provided.draggableProps.style?.isDragging ? 'bg-blue-100/80 shadow-md' : ''}`}
          >
            {/* Drag handle */}
            <div
              {...provided.dragHandleProps}
              className="mt-1 flex cursor-grab items-center justify-center text-slate-400 hover:text-slate-600 active:cursor-grabbing"
            >
              <GripVertical size={16} />
            </div>

            {/* Visit order indicator */}
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
              {stop.visitOrder}
            </div>

      {/* Stop details */}
      <div className="flex-1 min-w-0 space-y-1.5">
        {/* Place ID and type badge */}
        <div className="flex items-center gap-2 pr-6">
          <span className="text-sm font-medium text-slate-800 truncate">
            {stop.locationName || `Place: ${stop.googlePlaceId}`}
          </span>
          <Badge
            variant="outline"
            className={`text-[10px] ${stopTypeStyles[stop.stopType] ?? ''}`}
          >
            {stop.stopType.toLowerCase()}
          </Badge>
          {isDraft && !isAiModified && (
            <Badge variant="secondary" className="text-[9px] h-4 bg-blue-100 text-blue-700">Unsaved</Badge>
          )}
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

      {/* AI Stamp */}
      {isAiModified && (
        <div className="absolute top-3 right-3 text-blue-500 opacity-80" title="AI Suggested">
          <Sparkles size={16} className="fill-blue-500/20" />
        </div>
      )}

      {/* Action buttons — visible on hover */}
      <div className={`flex flex-col gap-1 transition-opacity ${isAiModified ? 'mt-6 opacity-0 group-hover:opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-slate-400 hover:text-blue-600"
          onClick={() => setIsEditOpen(true)}
        >
          <Pencil size={14} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-red-400 hover:text-red-600"
          onClick={() => onRemove(stop.id)}
        >
          <Trash2 size={14} />
        </Button>
      </div>
    </div>

    <EditStopDialog
      stop={stop}
      isOpen={isEditOpen}
      onClose={() => setIsEditOpen(false)}
      onSave={onUpdate}
    />
    </>
  )}
  </Draggable>
  )
}