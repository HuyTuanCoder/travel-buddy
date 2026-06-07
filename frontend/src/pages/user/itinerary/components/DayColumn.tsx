import React from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import StopCard from './StopCard'
import type {
  ItineraryDayResponse,
  AddStopRequest,
  StopType,
} from '@/types/itineraryTypes'

// ==================== Props ====================

interface DayColumnProps {
  day: ItineraryDayResponse
  onRemoveDay: (dayId: string) => void
  onAddStop: (dayId: string, payload: AddStopRequest) => void
  onRemoveStop: (stopId: string) => void
  isAddStopOpen: boolean
  onToggleAddStop: () => void
}

// ==================== Component ====================

export default function DayColumn({
  day,
  onRemoveDay,
  onAddStop,
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

  // Handle inline add-stop form submission
  const handleAddStopSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const payload: AddStopRequest = {
      googlePlaceId: formData.get('googlePlaceId') as string,
      stopType: (formData.get('stopType') as StopType) || 'ATTRACTION',
    }
    onAddStop(day.id, payload)
  }

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
        <div className="space-y-3">
          {day.stops.map((stop) => (
            <StopCard
              key={stop.id}
              stop={stop}
              onRemove={onRemoveStop}
            />
          ))}
        </div>
      )}

      {/* --- Inline add stop form --- */}
      {isAddStopOpen && (
        <form
          className="mt-4 space-y-3 rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-4"
          onSubmit={handleAddStopSubmit}
        >
          <p className="text-xs font-medium text-slate-600 uppercase tracking-wider">
            Add a stop
          </p>
          <input
            name="googlePlaceId"
            placeholder="Google Place ID"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
            required
          />
          <select
            name="stopType"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
            defaultValue="ATTRACTION"
          >
            <option value="ATTRACTION">Attraction</option>
            <option value="RESTAURANT">Restaurant</option>
            <option value="LODGING">Lodging</option>
            <option value="TRANSIT">Transit</option>
          </select>
          <div className="flex gap-2 pt-1">
            <Button type="submit" size="sm">
              Add
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onToggleAddStop}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}
    </div>
  )
}


