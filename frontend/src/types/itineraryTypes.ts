// ==================== Enums (type — unions can't be interfaces) ====================

export type ItineraryStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED'
export type MemberRole = 'OWNER' | 'EDITOR' | 'VIEWER'
export type StopType = 'ATTRACTION' | 'LODGING' | 'RESTAURANT' | 'TRANSIT'

// ==================== Itinerary CRUD ====================

export interface CreateItineraryRequest {
  title: string
  timezone: string
}

export interface UpdateItineraryRequest {
  title?: string
  timezone?: string
  status?: ItineraryStatus
}

export interface ItineraryResponse {
  id: string
  ownerId: string
  title: string
  status: ItineraryStatus
  timezone: string
  createdAt: string
  updatedAt: string
}

export interface ItinerarySummaryResponse {
  id: string
  title: string
  status: ItineraryStatus
  timezone: string
  role: MemberRole
  createdAt: string
}

// --- Nested types used in the detail view ---

export interface TripStopResponse {
  id: string
  googlePlaceId: string
  visitOrder: number
  arrivalTime: string | null
  departureTime: string | null
  stopType: StopType
  estimatedCost: number | null
  userNotes: string | null
  isDraftDeleted?: boolean
  // Fields populated by the Location Service
  locationName?: string
  address?: string
  latitude?: number
  longitude?: number
  imageUrl?: string
}

export interface ItineraryDayResponse {
  id: string
  dayNumber: number
  scheduledDate: string | null
  stops: TripStopResponse[]
  isDraftDeleted?: boolean
}

export interface ItineraryMemberResponse {
  userId: string
  role: MemberRole
  joinedAt: string
}

export interface ItineraryDetailResponse {
  id: string
  ownerId: string
  title: string
  status: ItineraryStatus
  timezone: string
  createdAt: string
  updatedAt: string
  members: ItineraryMemberResponse[]
  days: ItineraryDayResponse[]
}

// ==================== Group & Invitations ====================

export interface InviteRequest {
  inviteeUserId: string
  role: MemberRole
}

export interface InvitationActionRequest {
  action: 'ACCEPTED' | 'DECLINED'
}

export interface InvitationResponse {
  id: string
  itineraryId: string
  userId: string
  role: MemberRole
  invitedAt: string
}

export interface MemberListResponse {
  members: ItineraryMemberResponse[]
  pendingInvitations: InvitationResponse[]
}

// ==================== Day Management ====================

export interface AddDayRequest {
  scheduledDate?: string | null
}

// ==================== Stop Management ====================

export interface AddStopRequest {
  googlePlaceId: string
  stopType: StopType
  arrivalTime?: string | null
  departureTime?: string | null
  estimatedCost?: number | null
  userNotes?: string | null
}

export interface UpdateStopRequest {
  googlePlaceId?: string
  stopType?: StopType
  arrivalTime?: string | null
  departureTime?: string | null
  estimatedCost?: number | null
  userNotes?: string | null
}

export interface ReorderStopsRequest {
  stopIds: string[]
}
