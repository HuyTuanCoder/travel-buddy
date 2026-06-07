import { useParams, Link } from 'react-router-dom'
import { APIProvider } from '@vis.gl/react-google-maps'
import { DragDropContext } from '@hello-pangea/dnd'
import type { DropResult } from '@hello-pangea/dnd'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { useItineraryDetailLogic } from './hooks/useItineraryDetailLogic'
import DayColumn from './components/DayColumn'
import MemberPanel from './components/MemberPanel'
import TripMapVisualizer from './components/TripMapVisualizer'

// ==================== Status badge styles (same as TripCard) ====================

const statusStyles: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-600 border-slate-200',
  ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  ARCHIVED: 'bg-amber-50 text-amber-700 border-amber-200',
}

// ==================== Page ====================

export default function ItineraryDetailPage() {
  // Extract itinerary ID from the URL
  const { id } = useParams<{ id: string }>()

  const {
    itinerary,
    members,
    isLoading,
    error,
    handleUpdateItinerary,
    handleDeleteItinerary,
    handleAddDay,
    handleRemoveDay,
    addStopDayId,
    setAddStopDayId,
    handleAddStop,
    handleUpdateStop,
    handleRemoveStop,
    handleReorderStops,
    handleInvite,
    handleRemoveMember,
    handleUpdateMemberRole,
    handleTransferOwnership,
  } = useItineraryDetailLogic(id!)

  const onDragEnd = (result: DropResult) => {
    const { source, destination } = result
    if (!destination) return

    if (
      source.droppableId === destination.droppableId &&
      source.index === destination.index
    ) {
      return
    }

    if (source.droppableId !== destination.droppableId) {
      alert('Moving stops between days is not yet supported.')
      return
    }

    if (!itinerary) return

    const day = itinerary.days.find((d) => d.id === source.droppableId)
    if (!day) return

    const newStops = Array.from(day.stops)
    const [movedStop] = newStops.splice(source.index, 1)
    newStops.splice(destination.index, 0, movedStop)

    const stopIds = newStops.map((s) => s.id)
    handleReorderStops(source.droppableId, { stopIds })
  }

  // --- Loading state ---
  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-12 space-y-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-6 w-48" />
          <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
            <div className="space-y-4">
              <Skeleton className="h-48 rounded-2xl" />
              <Skeleton className="h-48 rounded-2xl" />
            </div>
            <Skeleton className="h-72 rounded-2xl" />
          </div>
        </div>
      </main>
    )
  }

  // --- Error or not found ---
  if (!itinerary) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-slate-700">
            {error ?? 'Trip not found'}
          </h2>
          <Link to="/trips" className="text-sm text-blue-600 mt-2 inline-block">
            ← Back to trips
          </Link>
        </div>
      </main>
    )
  }

  return (
    <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''}>
      <main className="min-h-screen bg-slate-50 text-slate-900">
        <div className="mx-auto max-w-6xl px-6 py-12">
        {/* --- Breadcrumb --- */}
        <Link
          to="/trips"
          className="text-xs text-slate-400 hover:text-blue-600 transition-colors"
        >
          ← All trips
        </Link>

        {/* --- Trip header --- */}
        <div className="flex items-start justify-between mt-4 mb-8">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-semibold text-slate-900">
                {itinerary.title}
              </h1>
              <Badge
                variant="outline"
                className={statusStyles[itinerary.status] ?? ''}
              >
                {itinerary.status.toLowerCase()}
              </Badge>
            </div>
            <p className="text-sm text-slate-500">
              {itinerary.timezone} · {itinerary.days.length} day
              {itinerary.days.length !== 1 ? 's' : ''}
            </p>
          </div>

          {/* Trip actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleUpdateItinerary({
                  status: itinerary.status === 'ACTIVE' ? 'ARCHIVED' : 'ACTIVE',
                })
              }
            >
              {itinerary.status === 'ACTIVE' ? 'Archive' : 'Activate'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-red-500 border-red-200 hover:bg-red-50"
              onClick={handleDeleteItinerary}
            >
              Delete
            </Button>
          </div>
        </div>

        {/* --- Error banner --- */}
        {error && (
          <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {error}
          </div>
        )}

        <Separator className="mb-8" />

        {/* --- Main content: timeline + map --- */}
        <div className="grid gap-8 lg:grid-cols-[450px_1fr]">
          {/* Left: day timeline & members */}
          <div className="space-y-6">
            <div className="space-y-5">
              <DragDropContext onDragEnd={onDragEnd}>
                {itinerary.days.map((day) => (
                  <DayColumn
                    key={day.id}
                    day={day}
                    onRemoveDay={handleRemoveDay}
                    onAddStop={handleAddStop}
                    onUpdateStop={handleUpdateStop}
                    onRemoveStop={handleRemoveStop}
                    isAddStopOpen={addStopDayId === day.id}
                    onToggleAddStop={() =>
                      setAddStopDayId(addStopDayId === day.id ? null : day.id)
                    }
                  />
                ))}
              </DragDropContext>

              {/* Add day button */}
              <Button
                variant="outline"
                className="w-full border-dashed border-slate-300 text-slate-500 hover:text-slate-700 hover:border-slate-400"
                onClick={() => handleAddDay({ scheduledDate: null })}
              >
                + Add day {itinerary.days.length + 1}
              </Button>
            </div>

            {/* Members panel */}
            {members && (
              <MemberPanel
                members={members}
                onInvite={handleInvite}
                onRemoveMember={handleRemoveMember}
                onUpdateRole={handleUpdateMemberRole}
                onTransferOwnership={handleTransferOwnership}
              />
            )}
          </div>

          {/* Right: sticky map visualizer */}
          <div className="hidden lg:block relative">
            <div className="sticky top-6 h-[calc(100vh-6rem)]">
              <TripMapVisualizer itinerary={itinerary} />
            </div>
          </div>
        </div>
        </div>
      </main>
    </APIProvider>
  )
}


