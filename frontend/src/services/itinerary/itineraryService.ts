import api from '../api'
import type {
  CreateItineraryRequest,
  UpdateItineraryRequest,
  ItineraryResponse,
  ItinerarySummaryResponse,
  ItineraryDetailResponse,
} from '@/types/itineraryTypes'

// ==================== POST /itineraries ====================

export const createItinerary = async (
  payload: CreateItineraryRequest,
): Promise<ItineraryResponse> => {
  try {
    const response = await api.post('/itineraries', payload)
    return response.data as ItineraryResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== GET /itineraries ====================

export const listItineraries = async (): Promise<ItinerarySummaryResponse[]> => {
  try {
    const response = await api.get('/itineraries')
    return response.data as ItinerarySummaryResponse[]
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== GET /itineraries/{id} ====================

export const getItineraryDetail = async (
  itineraryId: string,
): Promise<ItineraryDetailResponse> => {
  try {
    const response = await api.get(`/itineraries/${itineraryId}`)
    return response.data as ItineraryDetailResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== PUT /itineraries/{id} ====================

export const updateItinerary = async (
  itineraryId: string,
  payload: UpdateItineraryRequest,
): Promise<ItineraryResponse> => {
  try {
    const response = await api.put(`/itineraries/${itineraryId}`, payload)
    return response.data as ItineraryResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== DELETE /itineraries/{id} ====================

export const deleteItinerary = async (itineraryId: string): Promise<void> => {
  try {
    await api.delete(`/itineraries/${itineraryId}`)
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== POST /itineraries/{id}/batch-update ====================

export const batchUpdateItinerary = async (
  itineraryId: string,
  payload: { days: any[] },
): Promise<ItineraryDetailResponse> => {
  try {
    const response = await api.post(`/itineraries/${itineraryId}/batch-update`, payload)
    return response.data as ItineraryDetailResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}
