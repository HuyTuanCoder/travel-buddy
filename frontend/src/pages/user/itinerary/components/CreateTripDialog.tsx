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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const COMMON_TIMEZONES = [
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Anchorage',
  'Pacific/Honolulu',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Dubai',
  'Asia/Tokyo',
  'Asia/Singapore',
  'Australia/Sydney',
  'Pacific/Auckland',
  'UTC'
]

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

export default function CreateTripDialog({
  open,
  onOpenChange,
  form,
  onFieldChange,
  onSubmit,
  isSubmitting,
}: CreateTripDialogProps) {
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



          <div className="space-y-2">
            <Label htmlFor="trip-timezone">Destination Timezone</Label>
            <Select
              value={form.timezone}
              onValueChange={(val) => onFieldChange('timezone', val)}
            >
              <SelectTrigger id="trip-timezone">
                <SelectValue placeholder="Select a timezone" />
              </SelectTrigger>
              <SelectContent>
                {COMMON_TIMEZONES.map((tz) => (
                  <SelectItem key={tz} value={tz}>
                    {tz}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-slate-400">
              Crucial for accurate AI scheduling and calendar syncing.
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