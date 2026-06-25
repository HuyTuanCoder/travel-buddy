import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getItineraryDetail, updateItinerary, deleteItinerary, batchUpdateItinerary } from '@/services/itinerary/itineraryService'
import { getMembers, inviteMember, removeMember, updateMemberRole, transferOwnership } from '@/services/itinerary/memberService'
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
  draftItinerary: ItineraryDetailResponse | null
  modifiedStops: Record<string, { isAiModified?: boolean; isUserModified?: boolean }>
  members: MemberListResponse | null
  isLoading: boolean
  error: string | null
}

// ==================== Hook ====================

export function useItineraryDetailLogic(itineraryId: string) {
  const [state, setState] = useState<DetailState>({
    itinerary: null,
    draftItinerary: null,
    modifiedStops: {},
    members: null,
    isLoading: true,
    error: null,
  })

  // --- Track which day is expanded for adding stops ---
  const [addStopDayId, setAddStopDayId] = useState<string | null>(null)

  const navigate = useNavigate()

  // ==================== Data Fetching ====================

  // Fetch full itinerary detail (days, stops, members)
  const fetchDetail = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      const [detail, memberList] = await Promise.all([
        getItineraryDetail(itineraryId),
        getMembers(itineraryId),
      ])
      setState({
        itinerary: detail,
        draftItinerary: JSON.parse(JSON.stringify(detail)), // Deep clone for draft
        modifiedStops: {}, // Reset modifications on fresh fetch
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
  }, [itineraryId, navigate])

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

  // ==================== Draft / Co-Drafting Actions ====================

  // Apply an AI or User modification to the local draft state only
  const handleDraftUpdate = (
    updater: (draft: ItineraryDetailResponse) => void,
    stopIds: string[],
    source: 'AI' | 'USER'
  ) => {
    setState((prev) => {
      if (!prev.draftItinerary) return prev
      
      const newDraft = JSON.parse(JSON.stringify(prev.draftItinerary))
      updater(newDraft)

      const newModifiedStops = { ...prev.modifiedStops }
      stopIds.forEach(id => {
        if (!newModifiedStops[id]) newModifiedStops[id] = {}
        if (source === 'AI') newModifiedStops[id].isAiModified = true
        if (source === 'USER') newModifiedStops[id].isUserModified = true
      })

      return { ...prev, draftItinerary: newDraft, modifiedStops: newModifiedStops }
    })
  }

  // Local Reorder (Drag and Drop)
  const handleDraftReorderStops = (dayId: string, sourceIndex: number, destIndex: number) => {
    setState((prev) => {
      if (!prev.draftItinerary) return prev
      const newDraft = JSON.parse(JSON.stringify(prev.draftItinerary))
      const day = newDraft.days.find((d: any) => d.id === dayId)
      if (!day) return prev

      const [movedStop] = day.stops.splice(sourceIndex, 1)
      day.stops.splice(destIndex, 0, movedStop)

      // Mark the moved stop as user modified
      const newModifiedStops = { ...prev.modifiedStops }
      if (!newModifiedStops[movedStop.id]) newModifiedStops[movedStop.id] = {}
      newModifiedStops[movedStop.id].isUserModified = true

      return { ...prev, draftItinerary: newDraft, modifiedStops: newModifiedStops }
    })
  }

  // Local Add Stop
  const handleDraftAddStop = (dayId: string, stop: any, source: 'AI' | 'USER') => {
    const tempId = stop.id || `temp-${Date.now()}`
    const stopWithId = { ...stop, id: tempId }
    handleDraftUpdate((draft) => {
      const day = draft.days.find(d => d.id === dayId)
      if (day) day.stops.push(stopWithId)
    }, [tempId], source)
  }

  // Local Update Stop
  const handleDraftUpdateStop = (stopId: string, payload: any, source: 'AI' | 'USER') => {
    handleDraftUpdate((draft) => {
      for (const day of draft.days) {
        const idx = day.stops.findIndex(s => s.id === stopId)
        if (idx !== -1) {
          day.stops[idx] = { ...day.stops[idx], ...payload }
          break
        }
      }
    }, [stopId], source)
  }

  // Local Remove Stop
  const handleDraftRemoveStop = (stopId: string) => {
    setState((prev) => {
      if (!prev.draftItinerary) return prev
      const newDraft = JSON.parse(JSON.stringify(prev.draftItinerary))
      for (const day of newDraft.days) {
        day.stops = day.stops.filter((s: any) => s.id !== stopId)
      }
      return { ...prev, draftItinerary: newDraft }
    })
  }

  // Discard all local drafts and revert to pristine DB state
  const handleDraftDiscard = () => {
    setState((prev) => ({
      ...prev,
      draftItinerary: prev.itinerary ? JSON.parse(JSON.stringify(prev.itinerary)) : null,
      modifiedStops: {}
    }))
  }

  // Save drafts by pushing the entire draftItinerary to the backend batch-update
  const handleDraftSave = async () => {
    if (!state.draftItinerary) return

    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      const payload = {
        days: state.draftItinerary.days.map((day) => ({
          dayId: day.id,
          stops: day.stops.map((stop: any) => ({
            id: stop.id,
            googlePlaceId: stop.googlePlaceId,
            locationName: stop.locationName,
            address: stop.address,
            stopType: stop.stopType,
            userNotes: stop.userNotes,
            arrivalTime: stop.arrivalTime,
            departureTime: stop.departureTime,
            estimatedCost: stop.estimatedCost,
          })),
        })),
      }

      const updatedDetail = await batchUpdateItinerary(itineraryId, payload)
      setState((prev) => ({
        ...prev,
        itinerary: updatedDetail,
        draftItinerary: JSON.parse(JSON.stringify(updatedDetail)),
        modifiedStops: {},
        isLoading: false,
      }))
    } catch (err: any) {
      console.error('Failed to save drafts:', err)
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err.message || 'Failed to save drafts.',
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

  // Update a member's role
  const handleUpdateMemberRole = async (targetUserId: string, role: string) => {
    try {
      await updateMemberRole(itineraryId, targetUserId, role)
      const memberList = await getMembers(itineraryId)
      setState((prev) => ({ ...prev, members: memberList }))
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to update member role.',
      }))
    }
  }

  // Transfer ownership to another member
  const handleTransferOwnership = async (targetUserId: string) => {
    try {
      await transferOwnership(itineraryId, targetUserId)
      const memberList = await getMembers(itineraryId)
      setState((prev) => ({ ...prev, members: memberList }))
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err?.message ?? 'Failed to transfer ownership.',
      }))
    }
  }

  return {
    // State
    itinerary: state.itinerary,
    draftItinerary: state.draftItinerary,
    modifiedStops: state.modifiedStops,
    members: state.members,
    isLoading: state.isLoading,
    error: state.error,

    // Itinerary actions
    handleUpdateItinerary,
    handleDeleteItinerary,

    // Day actions
    handleAddDay,
    handleRemoveDay,

    // Stop actions (DB)
    addStopDayId,
    setAddStopDayId,
    handleAddStop,
    handleUpdateStop,
    handleRemoveStop,
    handleReorderStops,

    // Draft Actions (UI Overlay)
    handleDraftReorderStops,
    handleDraftAddStop,
    handleDraftUpdateStop,
    handleDraftRemoveStop,
    handleDraftDiscard,
    handleDraftSave,

    // Member actions
    handleInvite,
    handleRemoveMember,
    handleUpdateMemberRole,
    handleTransferOwnership,

    // Utilities
    refetch: fetchDetail,
  }
}
