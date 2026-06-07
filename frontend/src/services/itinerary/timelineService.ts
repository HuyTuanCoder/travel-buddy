import api from '../api'
import type {
  AddDayRequest,
  AddStopRequest,
  UpdateStopRequest,
  ReorderStopsRequest,
  ItineraryDayResponse,
  TripStopResponse,
} from '@/types/itineraryTypes'

// ==================== POST /itineraries/{id}/days ====================

export const addDay = async (
  itineraryId: string,
  payload: AddDayRequest,
): Promise<ItineraryDayResponse> => {
  try {
    const response = await api.post(
      `/itineraries/${itineraryId}/days`,
      payload,
    )
    return response.data as ItineraryDayResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== DELETE /itineraries/days/{dayId} ====================

export const removeDay = async (dayId: string): Promise<void> => {
  try {
    await api.delete(`/itineraries/days/${dayId}`)
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== POST /itineraries/days/{dayId}/stops ====================

export const addStop = async (
  dayId: string,
  payload: AddStopRequest,
): Promise<TripStopResponse> => {
  try {
    const response = await api.post(
      `/itineraries/days/${dayId}/stops`,
      payload,
    )
    return response.data as TripStopResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== PUT /itineraries/stops/{stopId} ====================

export const updateStop = async (
  stopId: string,
  payload: UpdateStopRequest,
): Promise<TripStopResponse> => {
  try {
    const response = await api.put(
      `/itineraries/stops/${stopId}`,
      payload,
    )
    return response.data as TripStopResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== DELETE /itineraries/stops/{stopId} ====================

export const removeStop = async (stopId: string): Promise<void> => {
  try {
    await api.delete(`/itineraries/stops/${stopId}`)
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== PUT /itineraries/days/{dayId}/stops/reorder ====================

export const reorderStops = async (
  dayId: string,
  payload: ReorderStopsRequest,
): Promise<TripStopResponse[]> => {
  try {
    const response = await api.put(
      `/itineraries/days/${dayId}/stops/reorder`,
      payload,
    )
    return response.data as TripStopResponse[]
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}
