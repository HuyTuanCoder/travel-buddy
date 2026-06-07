import api from '../api'
import type {
  InviteRequest,
  InvitationActionRequest,
  InvitationResponse,
  MemberListResponse,
  ItineraryMemberResponse,
} from '@/types/itineraryTypes'

// ==================== GET /itineraries/{id}/members ====================

export const getMembers = async (
  itineraryId: string,
): Promise<MemberListResponse> => {
  try {
    const response = await api.get(`/itineraries/${itineraryId}/members`)
    return response.data as MemberListResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== POST /itineraries/{id}/invitations ====================

export const inviteMember = async (
  itineraryId: string,
  payload: InviteRequest,
): Promise<InvitationResponse> => {
  try {
    const response = await api.post(
      `/itineraries/${itineraryId}/invitations`,
      payload,
    )
    return response.data as InvitationResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== PUT /itineraries/invitations/{id}/respond ====================

export const respondToInvitation = async (
  invitationId: string,
  payload: InvitationActionRequest,
): Promise<ItineraryMemberResponse | { message: string }> => {
  try {
    const response = await api.put(
      `/itineraries/invitations/${invitationId}/respond`,
      payload,
    )
    return response.data
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== DELETE /itineraries/{id}/members/{userId} ====================

export const removeMember = async (
  itineraryId: string,
  targetUserId: string,
): Promise<void> => {
  try {
    await api.delete(
      `/itineraries/${itineraryId}/members/${targetUserId}`,
    )
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== PUT /itineraries/{id}/members/{userId}/role ====================

export const updateMemberRole = async (
  itineraryId: string,
  targetUserId: string,
  role: string,
): Promise<ItineraryMemberResponse> => {
  try {
    const response = await api.put(
      `/itineraries/${itineraryId}/members/${targetUserId}/role`,
      { role },
    )
    return response.data as ItineraryMemberResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

// ==================== PUT /itineraries/{id}/members/{userId}/transfer-ownership ====================

export const transferOwnership = async (
  itineraryId: string,
  targetUserId: string,
): Promise<ItineraryMemberResponse> => {
  try {
    const response = await api.put(
      `/itineraries/${itineraryId}/members/${targetUserId}/transfer-ownership`,
    )
    return response.data as ItineraryMemberResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}
