import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useItineraryListLogic } from './hooks/useItineraryListLogic'
import TripCard from './components/TripCard'
import CreateTripDialog from './components/CreateTripDialog'

// ==================== Page ====================

export default function ItineraryListPage() {
  const {
    trips,
    isLoading,
    error,
    isCreateOpen,
    setIsCreateOpen,
    createForm,
    updateCreateField,
    handleCreate,
    isCreating,
    handleDelete,
  } = useItineraryListLogic()

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-4xl px-6 py-12">
        {/* --- Page header --- */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-blue-600 mb-1">
              Travel Buddy
            </p>
            <h1 className="text-2xl font-semibold text-slate-900">
              Your trips
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Plan, organize, and explore together.
            </p>
          </div>
          <Button onClick={() => setIsCreateOpen(true)}>
            + New trip
          </Button>
        </div>

        {/* --- Error banner --- */}
        {error && (
          <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {error}
          </div>
        )}

        {/* --- Loading skeletons --- */}
        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-36 rounded-2xl" />
            ))}
          </div>
        )}

        {/* --- Empty state --- */}
        {!isLoading && trips.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="text-5xl mb-4">🗺️</div>
            <h2 className="text-lg font-semibold text-slate-700">
              No trips yet
            </h2>
            <p className="text-sm text-slate-500 mt-1 max-w-xs">
              Create your first trip to start planning your next adventure
              with friends.
            </p>
            <Button className="mt-6" onClick={() => setIsCreateOpen(true)}>
              Create your first trip
            </Button>
          </div>
        )}

        {/* --- Trip grid --- */}
        {!isLoading && trips.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {trips.map((trip) => (
              <TripCard
                key={trip.id}
                trip={trip}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* --- Create dialog --- */}
      <CreateTripDialog
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
        form={createForm}
        onFieldChange={updateCreateField}
        onSubmit={handleCreate}
        isSubmitting={isCreating}
      />
    </main>
  )
}


