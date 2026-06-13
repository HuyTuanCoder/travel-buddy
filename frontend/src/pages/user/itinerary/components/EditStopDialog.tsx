import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import type { TripStopResponse, UpdateStopRequest } from '@/types/itineraryTypes'

interface EditStopDialogProps {
  stop: TripStopResponse
  isOpen: boolean
  onClose: () => void
  onSave: (stopId: string, payload: UpdateStopRequest) => void
}

export default function EditStopDialog({
  stop,
  isOpen,
  onClose,
  onSave,
}: EditStopDialogProps) {
  const [stopType, setStopType] = useState<string>(stop.stopType || 'ATTRACTION')
  const [arrivalTime, setArrivalTime] = useState(stop.arrivalTime || '')
  const [departureTime, setDepartureTime] = useState(stop.departureTime || '')
  const [estimatedCost, setEstimatedCost] = useState<string>(
    stop.estimatedCost !== null ? String(stop.estimatedCost) : ''
  )
  const [userNotes, setUserNotes] = useState(stop.userNotes || '')

  useEffect(() => {
    if (isOpen) {
      setStopType(stop.stopType || 'ATTRACTION')
      setArrivalTime(stop.arrivalTime || '')
      setDepartureTime(stop.departureTime || '')
      setEstimatedCost(stop.estimatedCost !== null ? String(stop.estimatedCost) : '')
      setUserNotes(stop.userNotes || '')
    }
  }, [isOpen, stop])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Parse cost or default to null
    const costParsed = estimatedCost ? parseFloat(estimatedCost) : null

    onSave(stop.id, {
      stopType: stopType as any,
      arrivalTime: arrivalTime || null,
      departureTime: departureTime || null,
      estimatedCost: costParsed !== null && !isNaN(costParsed) ? costParsed : null,
      userNotes: userNotes || null,
    })
    
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Stop Details</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Stop Type</label>
            <select
              value={stopType}
              onChange={(e) => setStopType(e.target.value)}
              className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ATTRACTION">Attraction</option>
              <option value="RESTAURANT">Restaurant</option>
              <option value="LODGING">Lodging</option>
              <option value="TRANSIT">Transit</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Arrival Time</label>
              <input
                type="time"
                value={arrivalTime}
                onChange={(e) => setArrivalTime(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Departure Time</label>
              <input
                type="time"
                value={departureTime}
                onChange={(e) => setDepartureTime(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Estimated Cost ($)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="e.g. 50.00"
              value={estimatedCost}
              onChange={(e) => setEstimatedCost(e.target.value)}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Notes</label>
            <textarea
              rows={3}
              placeholder="Any details or confirmation numbers..."
              value={userNotes}
              onChange={(e) => setUserNotes(e.target.value)}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Save Changes</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}