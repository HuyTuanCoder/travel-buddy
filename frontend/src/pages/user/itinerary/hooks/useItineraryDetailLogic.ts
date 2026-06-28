import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getItineraryDetail, updateItinerary, deleteItinerary, batchUpdateItinerary } from '@/services/itinerary/itineraryService'
import { getMembers, inviteMember, removeMember, updateMemberRole, transferOwnership } from '@/services/itinerary/memberService'
import { addDay, removeDay, addStop, updateStop, removeStop, reorderStops, moveStop, swapDays } from '@/services/itinerary/timelineService'
import { applyDraftAction } from '../utils/draftReducer'
import type {
  ItineraryDetailResponse,
  MemberListResponse,
  UpdateItineraryRequest,
  AddDayRequest,
  AddStopRequest,
  UpdateStopRequest,
  InviteRequest,
  MemberRole,
} from '@/types/itineraryTypes'

// ==================== State shape ====================

interface DetailState {
  itinerary: ItineraryDetailResponse | null
  draftItinerary: ItineraryDetailResponse | null
  isDraftMode: boolean
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
    isDraftMode: false,
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
        isDraftMode: false, // Reset draft mode on fetch
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
    if (state.isDraftMode) {
      setState(prev => {
        if (!prev.draftItinerary) return prev
        const newDraft = JSON.parse(JSON.stringify(prev.draftItinerary))
        const tempDay = {
          id: `temp-day-${Date.now()}`,
          itineraryId,
          dayNumber: newDraft.days.length + 1,
          scheduledDate: payload.scheduledDate,
          stops: []
        }
        newDraft.days.push(tempDay)
        return { ...prev, draftItinerary: newDraft }
      })
      return
    }

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
    if (state.isDraftMode) {
      setState(prev => {
        if (!prev.draftItinerary) return prev
        const newDraft = JSON.parse(JSON.stringify(prev.draftItinerary))
        newDraft.days = newDraft.days.filter((d: any) => d.id !== dayId)
        return { ...prev, draftItinerary: newDraft }
      })
      return
    }

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

  // Unified Optimistic Drag and Drop (Handles Reorder and Move across Days for both modes)
  const apiDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleOptimisticDragDrop = (
    stopId: string,
    sourceDayId: string,
    destDayId: string,
    sourceIndex: number,
    destIndex: number
  ) => {
    let reorderedStopIds: string[] = [];

    // 1. Silent Acceptance: Instantly mutate the correct state (Draft or Normal)
    setState((prev) => {
      const targetItinerary = prev.isDraftMode ? prev.draftItinerary : prev.itinerary;
      if (!targetItinerary) return prev;
      
      const newItin = JSON.parse(JSON.stringify(targetItinerary));
      const sDay = newItin.days.find((d: any) => d.id === sourceDayId);
      const dDay = newItin.days.find((d: any) => d.id === destDayId);
      if (!sDay || !dDay) return prev;

      const [movedStop] = sDay.stops.splice(sourceIndex, 1);
      dDay.stops.splice(destIndex, 0, movedStop);
      
      if (sourceDayId === destDayId) {
        reorderedStopIds = sDay.stops.map((s: any) => s.id);
      }

      const newModifiedStops = { ...prev.modifiedStops };
      if (prev.isDraftMode) {
        if (!newModifiedStops[movedStop.id]) newModifiedStops[movedStop.id] = {};
        newModifiedStops[movedStop.id].isUserModified = true;
      }

      return prev.isDraftMode 
        ? { ...prev, draftItinerary: newItin, modifiedStops: newModifiedStops }
        : { ...prev, itinerary: newItin, draftItinerary: newItin }; // Sync draft in normal mode
    });

    // 2. If in Draft Mode, we do NOT hit the DB. We just let local state persist.
    if (state.isDraftMode) return;

    // 3. Normal Mode: Debounce the DB call to prevent race conditions on rapid dragging
    if (apiDebounceRef.current) clearTimeout(apiDebounceRef.current);
    apiDebounceRef.current = setTimeout(async () => {
      try {
        if (sourceDayId === destDayId) {
          if (reorderedStopIds.length > 0) {
            await reorderStops(sourceDayId, { stopIds: reorderedStopIds });
          }
        } else {
          // Cross-day move
          await moveStop(stopId, { targetDayId: destDayId, targetVisitOrder: destIndex + 1 });
        }
        // Do NOT fetchDetail() here to avoid breaking the user's flow. Silent success!
      } catch (err: any) {
        console.error('Optimistic drag drop failed, reverting state.', err);
        fetchDetail(); // Revert to source of truth on error
      }
    }, 500);
  }

  // Swap Days (Optimistic)
  const handleSwapDays = (dayA: number, dayB: number) => {
    setState((prev) => {
      const targetItinerary = prev.isDraftMode ? prev.draftItinerary : prev.itinerary;
      if (!targetItinerary) return prev;
      
      const newItin = JSON.parse(JSON.stringify(targetItinerary));
      const dayAIndex = newItin.days.findIndex((d: any) => d.dayNumber === dayA);
      const dayBIndex = newItin.days.findIndex((d: any) => d.dayNumber === dayB);
      if (dayAIndex !== -1 && dayBIndex !== -1) {
        const temp = newItin.days[dayAIndex].dayNumber;
        newItin.days[dayAIndex].dayNumber = newItin.days[dayBIndex].dayNumber;
        newItin.days[dayBIndex].dayNumber = temp;
      }
      newItin.days.sort((a: any, b: any) => a.dayNumber - b.dayNumber);

      return prev.isDraftMode 
        ? { ...prev, draftItinerary: newItin }
        : { ...prev, itinerary: newItin, draftItinerary: newItin };
    });

    if (state.isDraftMode) return;

    if (apiDebounceRef.current) clearTimeout(apiDebounceRef.current);
    apiDebounceRef.current = setTimeout(async () => {
      try {
        await swapDays(itineraryId, { dayA, dayB });
      } catch (err: any) {
        console.error('Swap days failed, reverting state.', err);
        fetchDetail();
      }
    }, 500);
  }

  // ==================== Draft / Co-Drafting Actions ====================

  const toggleDraftMode = (force?: boolean) => {
    setState((prev) => ({
      ...prev,
      isDraftMode: force !== undefined ? force : !prev.isDraftMode
    }))
  }

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

      return { ...prev, isDraftMode: true, draftItinerary: newDraft, modifiedStops: newModifiedStops }
    })
  }



  // Unified React Draft Dispatcher
  const dispatchDraftActions = useCallback((actions: any[]) => {
    setState((prev) => {
      if (!prev.draftItinerary) return prev;
      const newDraft = JSON.parse(JSON.stringify(prev.draftItinerary));
      const newModifiedStops = { ...prev.modifiedStops };

      for (const action of actions) {
        applyDraftAction(newDraft, action, newModifiedStops, itineraryId);
      }

      // Sort days by dayNumber so UI reflects swaps properly
      newDraft.days.sort((a: any, b: any) => a.dayNumber - b.dayNumber);

      return { ...prev, isDraftMode: true, draftItinerary: newDraft, modifiedStops: newModifiedStops };
    });
  }, [itineraryId]);

  // Discard all local drafts and revert to pristine DB state
  const handleDraftDiscard = () => {
    setState((prev) => ({
      ...prev,
      draftItinerary: prev.itinerary ? JSON.parse(JSON.stringify(prev.itinerary)) : null,
      isDraftMode: false,
      modifiedStops: {}
    }))
  }

  // Save drafts by pushing the entire draftItinerary to the backend batch-update
  const handleDraftSave = async () => {
    if (!state.draftItinerary) return

    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      // 1. Strip Ghosts
      const validDays = state.draftItinerary.days.filter((d: any) => !d.isDraftDeleted);

      // 2. Re-Index Days and Stops
      const payload = {
        days: validDays.map((day: any, dayIndex: number) => {
          const validStops = day.stops.filter((s: any) => !s.isDraftDeleted);
          return {
            dayId: day.id,
            dayNumber: dayIndex + 1, // Force sequence!
            stops: validStops.map((stop: any, stopIndex: number) => ({
              id: stop.id,
              visitOrder: stopIndex + 1, // Force sequence!
              googlePlaceId: stop.googlePlaceId,
              locationName: stop.locationName,
              address: stop.address,
              stopType: stop.stopType,
              userNotes: stop.userNotes,
              arrivalTime: stop.arrivalTime,
              departureTime: stop.departureTime,
              estimatedCost: stop.estimatedCost,
            })),
          };
        }),
      }

      const updatedDetail = await batchUpdateItinerary(itineraryId, payload)
      setState((prev) => ({
        ...prev,
        itinerary: updatedDetail,
        draftItinerary: JSON.parse(JSON.stringify(updatedDetail)),
        isDraftMode: false,
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
    isDraftMode: state.isDraftMode,
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
    handleOptimisticDragDrop,
    handleSwapDays,

    // Draft Actions (UI Overlay)
    toggleDraftMode,
    dispatchDraftActions,
    handleDraftDiscard,
    handleDraftSave,
    handleDraftUpdate,

    // Member actions
    handleInvite,
    handleRemoveMember,
    handleUpdateMemberRole,
    handleTransferOwnership,

    // Utilities
    refetch: fetchDetail,
  }
}
