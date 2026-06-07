import { Droppable } from '@hello-pangea/dnd'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import StopCard from './StopCard'
import AddStopForm from './AddStopForm'
import type {
  ItineraryDayResponse,
  AddStopRequest,
  UpdateStopRequest,
} from '@/types/itineraryTypes'

// ==================== Props ====================

interface DayColumnProps {
  day: ItineraryDayResponse
  onRemoveDay: (dayId: string) => void
  onAddStop: (dayId: string, payload: AddStopRequest) => void
  onUpdateStop: (stopId: string, payload: UpdateStopRequest) => void
  onRemoveStop: (stopId: string) => void
  isAddStopOpen: boolean
  onToggleAddStop: () => void
}

// ==================== Component ====================

export default function DayColumn({
  day,
  onRemoveDay,
  onAddStop,
  onUpdateStop,
  onRemoveStop,
  isAddStopOpen,
  onToggleAddStop,
}: DayColumnProps) {
  // Format scheduled date if it exists
  const formattedDate = day.scheduledDate
    ? new Date(day.scheduledDate + 'T00:00:00').toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      })
    : null



  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      {/* --- Day header --- */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-200 font-semibold">
            Day {day.dayNumber}
          </Badge>
          {formattedDate && (
            <span className="text-sm text-slate-500">{formattedDate}</span>
          )}
        </div>

        {/* Day actions */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-slate-500 hover:text-slate-700"
            onClick={onToggleAddStop}
          >
            + Stop
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-red-400 hover:text-red-600"
            onClick={() => onRemoveDay(day.id)}
          >
            Remove
          </Button>
        </div>
      </div>

      <Separator className="mb-4" />

      {/* --- Stops list --- */}
      {day.stops.length === 0 && !isAddStopOpen ? (
        <p className="text-sm text-slate-400 italic py-4 text-center">
          No stops yet. Click "+ Stop" to add one.
        </p>
      ) : (
        <Droppable droppableId={day.id}>
          {(provided: any) => (
            <div
              className="space-y-3"
              ref={provided.innerRef}
              {...provided.droppableProps}
            >
              {day.stops.map((stop, index) => (
                <StopCard
                  key={stop.id}
                  stop={stop}
                  index={index}
                  onUpdate={onUpdateStop}
                  onRemove={onRemoveStop}
                />
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      )}

      {/* --- Inline add stop form --- */}
      {isAddStopOpen && (
        <AddStopForm
          dayId={day.id}
          onAddStop={onAddStop}
          onCancel={onToggleAddStop}
        />
      )}
    </div>
  )
}


