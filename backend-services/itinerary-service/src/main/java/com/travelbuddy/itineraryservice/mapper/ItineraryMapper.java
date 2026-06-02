package com.travelbuddy.itineraryservice.mapper;

import com.travelbuddy.itineraryservice.dto.*;
import com.travelbuddy.itineraryservice.model.*;
import org.springframework.stereotype.Component;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Component
public class ItineraryMapper {

  // --- Request → Entity ---

  // Converts a create request into a fresh Itinerary entity
  public Itinerary toEntity(CreateItineraryRequest request, String ownerId) {
    Itinerary itinerary = new Itinerary();
    itinerary.setOwnerId(ownerId);
    itinerary.setTitle(request.getTitle());
    itinerary.setTimezone(request.getTimezone());
    // status defaults to DRAFT via the entity, createdAt/updatedAt set by @PrePersist
    return itinerary;
  }

  // --- Entity → Response (metadata only, for POST/PUT) ---

  public ItineraryResponse toItineraryResponse(Itinerary itinerary) {
    ItineraryResponse response = new ItineraryResponse();
    response.setId(itinerary.getId());
    response.setOwnerId(itinerary.getOwnerId());
    response.setTitle(itinerary.getTitle());
    response.setStatus(itinerary.getStatus());
    response.setTimezone(itinerary.getTimezone());
    response.setCreatedAt(itinerary.getCreatedAt());
    response.setUpdatedAt(itinerary.getUpdatedAt());
    return response;
  }

  // --- Entity → Summary (for GET list, includes the user's role) ---

  public ItinerarySummaryResponse toSummaryResponse(ItineraryMember membership) {
    Itinerary itinerary = membership.getItinerary();
    ItinerarySummaryResponse response = new ItinerarySummaryResponse();
    response.setId(itinerary.getId());
    response.setTitle(itinerary.getTitle());
    response.setStatus(itinerary.getStatus());
    response.setTimezone(itinerary.getTimezone());
    response.setRole(membership.getRole());
    response.setCreatedAt(itinerary.getCreatedAt());
    return response;
  }

  // --- Entity → Full Detail (for GET /{id}, assembles the entire nested structure) ---

  public ItineraryDetailResponse toDetailResponse(Itinerary itinerary,
                                                   List<ItineraryMember> members,
                                                   List<ItineraryDay> days,
                                                   Map<UUID, List<TripStop>> stopsByDayId) {
    ItineraryDetailResponse response = new ItineraryDetailResponse();
    response.setId(itinerary.getId());
    response.setOwnerId(itinerary.getOwnerId());
    response.setTitle(itinerary.getTitle());
    response.setStatus(itinerary.getStatus());
    response.setTimezone(itinerary.getTimezone());
    response.setCreatedAt(itinerary.getCreatedAt());
    response.setUpdatedAt(itinerary.getUpdatedAt());

    // Map each member entity to its response shape
    response.setMembers(members.stream()
        .map(this::toMemberResponse)
        .collect(Collectors.toList()));

    // Map each day entity, attaching its stops from the pre-grouped map
    response.setDays(days.stream()
        .map(day -> toDayResponse(day, stopsByDayId.getOrDefault(day.getId(), Collections.emptyList())))
        .collect(Collectors.toList()));

    return response;
  }

  // --- Member / Invitation mappers (public — used by MemberService) ---

  public ItineraryMemberResponse toMemberResponse(ItineraryMember member) {
    ItineraryMemberResponse response = new ItineraryMemberResponse();
    response.setUserId(member.getUserId());
    response.setRole(member.getRole());
    response.setJoinedAt(member.getJoinedAt());
    return response;
  }

  public InvitationResponse toInvitationResponse(ItineraryInvitation invitation) {
    InvitationResponse response = new InvitationResponse();
    response.setId(invitation.getId());
    response.setItineraryId(invitation.getItinerary().getId());
    response.setUserId(invitation.getUserId());
    response.setRole(invitation.getRole());
    response.setInvitedAt(invitation.getInvitedAt());
    return response;
  }

  private ItineraryDayResponse toDayResponse(ItineraryDay day, List<TripStop> stops) {
    ItineraryDayResponse response = new ItineraryDayResponse();
    response.setId(day.getId());
    response.setDayNumber(day.getDayNumber());
    response.setScheduledDate(day.getScheduledDate());
    response.setStops(stops.stream()
        .map(this::toStopResponse)
        .collect(Collectors.toList()));
    return response;
  }

  private TripStopResponse toStopResponse(TripStop stop) {
    TripStopResponse response = new TripStopResponse();
    response.setId(stop.getId());
    response.setGooglePlaceId(stop.getGooglePlaceId());
    response.setVisitOrder(stop.getVisitOrder());
    response.setArrivalTime(stop.getArrivalTime());
    response.setDepartureTime(stop.getDepartureTime());
    response.setStopType(stop.getStopType());
    response.setEstimatedCost(stop.getEstimatedCost());
    response.setUserNotes(stop.getUserNotes());
    return response;
  }
}
