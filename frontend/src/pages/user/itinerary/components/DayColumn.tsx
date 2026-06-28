import { useState } from 'react'
import { Droppable } from '@hello-pangea/dnd'
import { RefreshCcw, GripVertical } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import StopCard from './StopCard'
import AddStopForm from './AddStopForm'
import DestructiveConfirmModal from './DestructiveConfirmModal'
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
  modifiedStops?: Record<string, { isAiModified?: boolean; isUserModified?: boolean }>
  isDraftMode?: boolean
  onRestoreDay?: (dayId: string) => void
  onRestoreStop?: (stopId: string) => void
  onHardRemoveStop?: (stopId: string) => void
  dragHandleProps?: any
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
  modifiedStops = {},
  isDraftMode,
  onRestoreDay,
  onRestoreStop,
  onHardRemoveStop,
  dragHandleProps,
}: DayColumnProps) {
  const [isRemoveDayModalOpen, setIsRemoveDayModalOpen] = useState(false)
  // Format scheduled date if it exists
  const formattedDate = day.scheduledDate
    ? new Date(day.scheduledDate + 'T00:00:00').toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      })
    : null



  return (
    <div className={`relative flex flex-col max-h-[70vh] rounded-2xl border bg-white p-5 transition-all ${day.isDraftDeleted ? 'opacity-50 border-slate-200 bg-slate-50' : 'border-slate-200'}`}>
      
      {/* If Day is Deleted, show Restore overlay */}
      {day.isDraftDeleted && onRestoreDay && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-50/50 rounded-2xl pointer-events-auto backdrop-blur-[1px]">
          <Button 
            variant="default" 
            size="lg" 
            className="bg-emerald-600 hover:bg-emerald-700 shadow-lg"
            onClick={() => onRestoreDay(day.id)}
          >
            <RefreshCcw size={16} className="mr-2" />
            Restore Day {day.dayNumber}
          </Button>
        </div>
      )}

      {/* --- Day header --- */}
      <div className={`flex items-center justify-between mb-4 ${day.isDraftDeleted ? 'pointer-events-none' : ''}`}>
        <div className="flex items-center gap-3">
          <div {...dragHandleProps} className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500">
            <GripVertical size={18} />
          </div>
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
            onClick={() => isDraftMode ? onRemoveDay(day.id) : setIsRemoveDayModalOpen(true)}
          >
            Remove
          </Button>
        </div>
      </div>

      <Separator className="mb-4" />

      {/* --- Stops list --- */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 -mr-2">
        {day.stops.length === 0 && !isAddStopOpen ? (
          <p className="text-sm text-slate-400 italic py-4 text-center">
            No stops yet. Click "+ Stop" to add one.
          </p>
        ) : (
          <Droppable droppableId={day.id}>
            {(provided: any) => (
              <div
                className="space-y-3 pb-4"
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
                    onRestore={onRestoreStop}
                    onHardRemove={onHardRemoveStop}
                    isDraft={!!modifiedStops[stop.id]}
                    isDraftMode={isDraftMode}
                    isAiModified={modifiedStops[stop.id]?.isAiModified}
                  />
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        )}

        {/* --- Inline add stop form --- */}
        {isAddStopOpen && (
          <div className="mt-4">
            <AddStopForm
              dayId={day.id}
              onAddStop={onAddStop}
              onCancel={onToggleAddStop}
            />
          </div>
        )}
      </div>
      
      <DestructiveConfirmModal 
        isOpen={isRemoveDayModalOpen} 
        onClose={() => setIsRemoveDayModalOpen(false)} 
        onConfirm={() => onRemoveDay(day.id)} 
        title={`Remove Day ${day.dayNumber}`}
        description="Are you sure you want to remove this day? This will permanently delete all stops on this day. This action cannot be undone."
      />
    </div>
  )
}


