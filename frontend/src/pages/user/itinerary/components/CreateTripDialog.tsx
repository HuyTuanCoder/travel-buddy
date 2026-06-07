import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

// ==================== Props ====================

interface CreateTripDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  form: { title: string; timezone: string }
  onFieldChange: (field: 'title' | 'timezone', value: string) => void
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void
  isSubmitting: boolean
}

// ==================== Component ====================

const CreateTripDialog = ({
  open,
  onOpenChange,
  form,
  onFieldChange,
  onSubmit,
  isSubmitting,
}: CreateTripDialogProps) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create a new trip</DialogTitle>
          <DialogDescription>
            Give your trip a name and we'll set up everything for you.
          </DialogDescription>
        </DialogHeader>

        <form className="space-y-5 pt-2" onSubmit={onSubmit}>
          {/* Trip title */}
          <div className="space-y-2">
            <Label htmlFor="trip-title">Trip name</Label>
            <Input
              id="trip-title"
              placeholder="Weekend in Tokyo"
              value={form.title}
              onChange={(e) => onFieldChange('title', e.target.value)}
              required
              autoFocus
            />
          </div>

          {/* Timezone — auto-detected, editable */}
          <div className="space-y-2">
            <Label htmlFor="trip-timezone">Timezone</Label>
            <Input
              id="trip-timezone"
              placeholder="America/New_York"
              value={form.timezone}
              onChange={(e) => onFieldChange('timezone', e.target.value)}
              required
            />
            <p className="text-xs text-slate-400">
              Auto-detected from your browser. Change if the trip is elsewhere.
            </p>
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create trip'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default CreateTripDialog
