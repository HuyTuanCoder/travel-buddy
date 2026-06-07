import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import LocationSearchInput from '@/components/ui/LocationSearchInput'
import type { AddStopRequest, StopType } from '@/types/itineraryTypes'

interface AddStopFormProps {
  dayId: string
  onAddStop: (dayId: string, payload: AddStopRequest) => void
  onCancel: () => void
}

export default function AddStopForm({
  dayId,
  onAddStop,
  onCancel,
}: AddStopFormProps) {
  const [stopType, setStopType] = useState<StopType>('ATTRACTION')
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null)
  const [selectedPlaceName, setSelectedPlaceName] = useState<string | null>(null)

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    
    if (!selectedPlaceId) {
      alert('Please select a location from the search dropdown.')
      return
    }

    const payload: AddStopRequest = {
      googlePlaceId: selectedPlaceId,
      stopType: stopType,
      arrivalTime: null,
      departureTime: null,
      estimatedCost: null,
      userNotes: null,
    }

    onAddStop(dayId, payload)
  }

  const handlePlaceSelected = (placeId: string, placeName: string) => {
    setSelectedPlaceId(placeId)
    setSelectedPlaceName(placeName)
  }

  return (
    <form
      className="mt-4 space-y-3 rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-4"
      onSubmit={handleSubmit}
    >
      <p className="text-xs font-medium text-slate-600 uppercase tracking-wider">
        Add a stop
      </p>

      {/* Location Search Input */}
      <div>
        <LocationSearchInput
          onPlaceSelected={handlePlaceSelected}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
        />
        {selectedPlaceName && (
          <p className="mt-1 text-xs text-emerald-600 font-medium">
            Selected: {selectedPlaceName}
          </p>
        )}
      </div>

      <select
        value={stopType}
        onChange={(e) => setStopType(e.target.value as StopType)}
        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
      >
        <option value="ATTRACTION">Attraction</option>
        <option value="RESTAURANT">Restaurant</option>
        <option value="LODGING">Lodging</option>
        <option value="TRANSIT">Transit</option>
      </select>

      <div className="flex gap-2 pt-1">
        <Button type="submit" size="sm" disabled={!selectedPlaceId}>
          Add
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onCancel}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}
