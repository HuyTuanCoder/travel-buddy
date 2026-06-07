import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  createItinerary,
  listItineraries,
  deleteItinerary,
} from '@/services/itinerary/itineraryService'
import type {
  ItinerarySummaryResponse,
  CreateItineraryRequest,
} from '@/types/itineraryTypes'

// ==================== State shape ====================

interface ItineraryListState {
  trips: ItinerarySummaryResponse[]
  isLoading: boolean
  error: string | null
}

interface CreateTripForm {
  title: string
  timezone: string
}

// ==================== Hook ====================

export function useItineraryListLogic() {
  // --- Core state ---
  const [state, setState] = useState<ItineraryListState>({
    trips: [],
    isLoading: true,
    error: null,
  })

  // --- Create trip dialog state ---
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<CreateTripForm>({
    title: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone, // auto-detect user timezone
  })
  const [isCreating, setIsCreating] = useState(false)

  const navigate = useNavigate()

  // --- Fetch all trips on mount ---
  async function fetchTrips() {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      const trips = await listItineraries()
      setState({ trips, isLoading: false, error: null })
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err?.message ?? 'Failed to load trips.',
      }))
    }
  }

  useEffect(() => {
    fetchTrips()
  }, [])

  // --- Create a new trip ---
  const updateCreateField = (
    field: keyof CreateTripForm,
    value: string,
  ) => {
    setCreateForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsCreating(true)

    try {
      const payload: CreateItineraryRequest = {
        title: createForm.title,
        timezone: createForm.timezone,
      }
      const created = await createItinerary(payload)

      // Reset form and close dialog
      setCreateForm({
        title: '',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      })
      setIsCreateOpen(false)

      // Navigate to the newly created trip
      navigate(`/trips/${created.id}`)
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to create trip.',
      }))
    } finally {
      setIsCreating(false)
    }
  }

  // --- Delete a trip (owner only) ---
  const handleDelete = async (itineraryId: string) => {
    try {
      await deleteItinerary(itineraryId)
      // Optimistic removal from local state
      setState((prev) => ({
        ...prev,
        trips: prev.trips.filter((t) => t.id !== itineraryId),
      }))
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to archive trip.',
      }))
    }
  }

  return {
    // List state
    trips: state.trips,
    isLoading: state.isLoading,
    error: state.error,

    // Create dialog state + handlers
    isCreateOpen,
    setIsCreateOpen,
    createForm,
    updateCreateField,
    handleCreate,
    isCreating,

    // Actions
    handleDelete,
    refetch: fetchTrips,
  }
}
