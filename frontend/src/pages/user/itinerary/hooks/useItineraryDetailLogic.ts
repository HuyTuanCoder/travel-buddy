import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getItineraryDetail, updateItinerary, deleteItinerary } from '@/services/itinerary/itineraryService'
import { getMembers, inviteMember, removeMember } from '@/services/itinerary/memberService'
import { addDay, removeDay, addStop, updateStop, removeStop, reorderStops } from '@/services/itinerary/timelineService'
import type {
  ItineraryDetailResponse,
  MemberListResponse,
  UpdateItineraryRequest,
  AddDayRequest,
  AddStopRequest,
  UpdateStopRequest,
  ReorderStopsRequest,
  InviteRequest,
  MemberRole,
} from '@/types/itineraryTypes'

// ==================== State shape ====================

interface DetailState {
  itinerary: ItineraryDetailResponse | null
  members: MemberListResponse | null
  isLoading: boolean
  error: string | null
}

// ==================== Hook ====================

export function useItineraryDetailLogic(itineraryId: string) {
  const [state, setState] = useState<DetailState>({
    itinerary: null,
    members: null,
    isLoading: true,
    error: null,
  })

  // --- Track which day is expanded for adding stops ---
  const [addStopDayId, setAddStopDayId] = useState<string | null>(null)

  const navigate = useNavigate()

  // ==================== Data Fetching ====================

  // Fetch full itinerary detail (days, stops, members)
  async function fetchDetail() {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      const [detail, memberList] = await Promise.all([
        getItineraryDetail(itineraryId),
        getMembers(itineraryId),
      ])
      setState({
        itinerary: detail,
        members: memberList,
        isLoading: false,
        error: null,
      })
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err?.message ?? 'Failed to load trip details.',
      }))
    }
  }

  useEffect(() => {
    fetchDetail()
  }, [fetchDetail])

  // ==================== Itinerary Actions ====================

  // Update trip settings (title, timezone, status)
  const handleUpdateItinerary = async (payload: UpdateItineraryRequest) => {
    try {
      await updateItinerary(itineraryId, payload)
      await fetchDetail() // Refetch to sync all nested data
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to update trip.',
      }))
    }
  }

  // Delete the entire trip and navigate back to list
  const handleDeleteItinerary = async () => {
    try {
      await deleteItinerary(itineraryId)
      navigate('/trips')
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to delete trip.',
      }))
    }
  }

  // ==================== Day Actions ====================

  // Append a new day to the timeline
  const handleAddDay = async (payload: AddDayRequest) => {
    try {
      await addDay(itineraryId, payload)
      await fetchDetail()
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to add day.',
      }))
    }
  }

  // Remove a day and its stops
  const handleRemoveDay = async (dayId: string) => {
    try {
      await removeDay(dayId)
      await fetchDetail()
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to remove day.',
      }))
    }
  }

  // ==================== Stop Actions ====================

  // Add a stop to a specific day
  const handleAddStop = async (dayId: string, payload: AddStopRequest) => {
    try {
      await addStop(dayId, payload)
      setAddStopDayId(null) // Close the add-stop form
      await fetchDetail()
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to add stop.',
      }))
    }
  }

  // Update a stop's details
  const handleUpdateStop = async (stopId: string, payload: UpdateStopRequest) => {
    try {
      await updateStop(stopId, payload)
      await fetchDetail()
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to update stop.',
      }))
    }
  }

  // Remove a stop
  const handleRemoveStop = async (stopId: string) => {
    try {
      await removeStop(stopId)
      await fetchDetail()
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to remove stop.',
      }))
    }
  }

  // Reorder stops within a day (drag-and-drop)
  const handleReorderStops = async (dayId: string, payload: ReorderStopsRequest) => {
    try {
      await reorderStops(dayId, payload)
      await fetchDetail()
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to reorder stops.',
      }))
    }
  }

  // ==================== Member Actions ====================

  // Invite a user to the trip
  const handleInvite = async (inviteeUserId: string, role: MemberRole) => {
    try {
      const payload: InviteRequest = { inviteeUserId, role }
      await inviteMember(itineraryId, payload)
      // Refetch members to show the new pending invitation
      const memberList = await getMembers(itineraryId)
      setState((prev) => ({ ...prev, members: memberList }))
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to invite member.',
      }))
    }
  }

  // Kick a member or leave the trip
  const handleRemoveMember = async (targetUserId: string) => {
    try {
      await removeMember(itineraryId, targetUserId)
      const memberList = await getMembers(itineraryId)
      setState((prev) => ({ ...prev, members: memberList }))
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to remove member.',
      }))
    }
  }

  return {
    // State
    itinerary: state.itinerary,
    members: state.members,
    isLoading: state.isLoading,
    error: state.error,

    // Itinerary actions
    handleUpdateItinerary,
    handleDeleteItinerary,

    // Day actions
    handleAddDay,
    handleRemoveDay,

    // Stop actions
    addStopDayId,
    setAddStopDayId,
    handleAddStop,
    handleUpdateStop,
    handleRemoveStop,
    handleReorderStops,

    // Member actions
    handleInvite,
    handleRemoveMember,

    // Utilities
    refetch: fetchDetail,
  }
}
