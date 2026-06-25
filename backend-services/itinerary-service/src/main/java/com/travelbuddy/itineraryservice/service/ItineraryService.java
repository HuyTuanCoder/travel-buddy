package com.travelbuddy.itineraryservice.service;

import com.travelbuddy.itineraryservice.dto.*;
import com.travelbuddy.itineraryservice.mapper.ItineraryMapper;
import com.travelbuddy.itineraryservice.model.*;
import com.travelbuddy.itineraryservice.repository.*;
import com.travelbuddy.itineraryservice.grpc.LocationGrpcClient;
import com.travelbuddy.location.grpc.PlaceInfo;
import jakarta.transaction.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class ItineraryService {

  private static final Logger log = LoggerFactory.getLogger(ItineraryService.class);

  private final ItineraryRepository itineraryRepository;
  private final ItineraryMemberRepository memberRepository;
  private final ItineraryInvitationRepository invitationRepository;
  private final ItineraryDayRepository dayRepository;
  private final TripStopRepository stopRepository;
  private final ItineraryMapper mapper;
  private final AccessGuard accessGuard;
  private final LocationGrpcClient locationGrpcClient;

  public ItineraryService(ItineraryRepository itineraryRepository,
                          ItineraryMemberRepository memberRepository,
                          ItineraryInvitationRepository invitationRepository,
                          ItineraryDayRepository dayRepository,
                          TripStopRepository stopRepository,
                          ItineraryMapper mapper,
                          AccessGuard accessGuard,
                          LocationGrpcClient locationGrpcClient) {
    this.itineraryRepository = itineraryRepository;
    this.memberRepository = memberRepository;
    this.invitationRepository = invitationRepository;
    this.dayRepository = dayRepository;
    this.stopRepository = stopRepository;
    this.mapper = mapper;
    this.accessGuard = accessGuard;
    this.locationGrpcClient = locationGrpcClient;
  }

  // ==================== POST /itineraries ====================

  @Transactional
  public ItineraryResponse createItinerary(CreateItineraryRequest request, String userId) {
    log.info("[createItinerary] >>> Input: {}, userId={}", request, userId);

    // 1. Map the request to a new itinerary entity and persist it
    Itinerary itinerary = mapper.toEntity(request, userId);
    Itinerary savedItinerary = itineraryRepository.save(itinerary);

    // 2. Auto-add the creator as an OWNER member (row existence = confirmed member)
    ItineraryMember ownerMember = new ItineraryMember();
    ownerMember.setItinerary(savedItinerary);
    ownerMember.setUserId(userId);
    ownerMember.setRole(MemberRole.OWNER);
    // joinedAt set automatically by @PrePersist
    memberRepository.save(ownerMember);

    // 3. Map to response and return
    ItineraryResponse response = mapper.toItineraryResponse(savedItinerary);
    log.info("[createItinerary] <<< Output: {}", response);
    return response;
  }

  // ==================== GET /itineraries ====================

  public List<ItinerarySummaryResponse> listItineraries(String userId) {
    log.info("[listItineraries] >>> Input: userId={}", userId);

    // Fetch all trips the user belongs to, with itinerary data eagerly loaded via JOIN FETCH
    // No status filter needed — if a row exists in the member table, they're confirmed
    List<ItineraryMember> memberships = memberRepository.findByUserIdWithItinerary(userId);

    // Map each membership to a summary card (itinerary metadata + user's role)
    List<ItinerarySummaryResponse> responses = memberships.stream()
        .map(mapper::toSummaryResponse)
        .collect(Collectors.toList());

    log.info("[listItineraries] <<< Output: {} itineraries found", responses.size());
    return responses;
  }

  // ==================== GET /itineraries/{id} ====================

  public ItineraryDetailResponse getItineraryDetail(UUID itineraryId, String userId) {
    log.info("[getItineraryDetail] >>> Input: itineraryId={}, userId={}", itineraryId, userId);

    // 1. Verify the itinerary exists
    Itinerary itinerary = accessGuard.findItinerary(itineraryId);

    // 2. Verify the user is a member of this trip (any role can view)
    accessGuard.verifyMembership(itineraryId, userId);

    // 3. Fetch all related data
    List<ItineraryMember> members = memberRepository.findByItineraryId(itineraryId);
    List<ItineraryDay> days = dayRepository.findByItineraryIdOrderByDayNumberAsc(itineraryId);

    // 4. Batch-fetch all stops for all days in one query, then group by day ID
    List<UUID> dayIds = days.stream().map(ItineraryDay::getId).collect(Collectors.toList());
    Map<UUID, List<TripStop>> stopsByDayId = dayIds.isEmpty()
        ? Map.of()
        : stopRepository.findByItineraryDayIdInOrderByVisitOrderAsc(dayIds).stream()
            .collect(Collectors.groupingBy(stop -> stop.getItineraryDay().getId()));

    // 5. Extract all unique googlePlaceIds from the stops and fetch location data
    List<String> googlePlaceIds = stopsByDayId.values().stream()
        .flatMap(List::stream)
        .map(TripStop::getGooglePlaceId)
        .filter(id -> id != null && !id.isEmpty())
        .distinct()
        .collect(Collectors.toList());

    Map<String, PlaceInfo> locationData = locationGrpcClient.fetchPlaces(googlePlaceIds);

    // 6. Assemble the full nested response, injecting location data into stops
    ItineraryDetailResponse response = mapper.toDetailResponse(itinerary, members, days, stopsByDayId, locationData);
    log.info("[getItineraryDetail] <<< Output: {}", response);
    return response;
  }

  // ==================== PUT /itineraries/{id} ====================

  @Transactional
  public ItineraryResponse updateItinerary(UUID itineraryId, UpdateItineraryRequest request, String userId) {
    log.info("[updateItinerary] >>> Input: itineraryId={}, {}, userId={}", itineraryId, request, userId);

    // 1. Verify the itinerary exists
    Itinerary itinerary = accessGuard.findItinerary(itineraryId);

    // 2. Verify the user has OWNER or EDITOR role
    accessGuard.verifyEditPermission(itineraryId, userId);

    // 3. Apply only the non-null fields from the request (partial update)
    if (request.getTitle() != null) {
      itinerary.setTitle(request.getTitle());
    }
    if (request.getTimezone() != null) {
      itinerary.setTimezone(request.getTimezone());
    }
    if (request.getStatus() != null) {
      itinerary.setStatus(request.getStatus());
    }

    // 4. Save and return — @PreUpdate handles updatedAt timestamp
    Itinerary updatedItinerary = itineraryRepository.save(itinerary);
    ItineraryResponse response = mapper.toItineraryResponse(updatedItinerary);
    log.info("[updateItinerary] <<< Output: {}", response);
    return response;
  }

  // ==================== BATCH UPDATE /itineraries/{id}/batch-update ====================

  @Transactional
  public ItineraryDetailResponse batchUpdateItinerary(UUID itineraryId, BatchUpdateItineraryRequest request, String userId) {
    log.info("[batchUpdateItinerary] >>> Input: itineraryId={}, userId={}", itineraryId, userId);

    // 1. Verify the itinerary exists
    Itinerary itinerary = accessGuard.findItinerary(itineraryId);

    // 2. Verify the user has OWNER or EDITOR role
    accessGuard.verifyEditPermission(itineraryId, userId);

    // 3. Fetch all days for validation
    List<ItineraryDay> itineraryDays = dayRepository.findByItineraryIdOrderByDayNumberAsc(itineraryId);
    Map<UUID, ItineraryDay> dayMap = itineraryDays.stream()
        .collect(Collectors.toMap(ItineraryDay::getId, day -> day));

    // 4. Process each day in the payload
    for (BatchUpdateDayRequest dayReq : request.getDays()) {
      ItineraryDay day = dayMap.get(dayReq.getDayId());
      if (day == null) {
        throw new IllegalArgumentException("Day ID " + dayReq.getDayId() + " does not belong to itinerary " + itineraryId);
      }

      // Gather all existing stops for this day
      List<TripStop> existingStops = stopRepository.findByItineraryDayIdOrderByVisitOrderAsc(day.getId());
      Map<UUID, TripStop> existingStopMap = existingStops.stream()
          .collect(Collectors.toMap(TripStop::getId, stop -> stop));

      // Gather all valid UUIDs from the incoming payload
      List<UUID> incomingStopIds = dayReq.getStops().stream()
          .map(req -> {
            try {
              return UUID.fromString(req.getId());
            } catch (IllegalArgumentException e) {
              return null; // temporary id
            }
          })
          .filter(id -> id != null)
          .collect(Collectors.toList());

      // Delete existing stops that are NOT in the incoming payload
      for (TripStop existingStop : existingStops) {
        if (!incomingStopIds.contains(existingStop.getId())) {
          stopRepository.delete(existingStop);
        }
      }

      // Process incoming stops
      int visitOrder = 0;
      for (BatchUpdateStopRequest stopReq : dayReq.getStops()) {
        TripStop stopToSave;
        UUID stopId = null;
        try {
          stopId = UUID.fromString(stopReq.getId());
        } catch (IllegalArgumentException e) {
          // It's a temp id
        }

        if (stopId != null && existingStopMap.containsKey(stopId)) {
          stopToSave = existingStopMap.get(stopId);
        } else {
          stopToSave = new TripStop();
          stopToSave.setItineraryDay(day);
        }

        // Update fields
        if (stopReq.getGooglePlaceId() == null || stopReq.getGooglePlaceId().isBlank()) {
          throw new IllegalArgumentException("googlePlaceId is required for all stops");
        }
        stopToSave.setGooglePlaceId(stopReq.getGooglePlaceId());
        stopToSave.setStopType(stopReq.getStopType());
        stopToSave.setVisitOrder(visitOrder++);
        stopToSave.setUserNotes(stopReq.getUserNotes());
        stopToSave.setArrivalTime(stopReq.getArrivalTime());
        stopToSave.setDepartureTime(stopReq.getDepartureTime());
        stopToSave.setEstimatedCost(stopReq.getEstimatedCost());

        stopRepository.save(stopToSave);
      }
    }

    // 5. Fetch and return the fully updated itinerary
    log.info("[batchUpdateItinerary] <<< Output: successfully reconciled itinerary {}", itineraryId);
    return getItineraryDetail(itineraryId, userId);
  }

  // ==================== DELETE /itineraries/{id} ====================

  @Transactional
  public void deleteItinerary(UUID itineraryId, String userId) {
    log.info("[deleteItinerary] >>> Input: itineraryId={}, userId={}", itineraryId, userId);

    // 1. Verify the itinerary exists
    Itinerary itinerary = accessGuard.findItinerary(itineraryId);

    // 2. Verify the user is the OWNER — only owners can delete a trip
    accessGuard.verifyOwnership(itineraryId, userId);

    // 3. Cascade delete in order: stops → days → invitations → members → itinerary
    List<ItineraryDay> days = dayRepository.findByItineraryIdOrderByDayNumberAsc(itineraryId);
    List<UUID> dayIds = days.stream().map(ItineraryDay::getId).collect(Collectors.toList());

    if (!dayIds.isEmpty()) {
      stopRepository.deleteByDayIds(dayIds);
    }
    dayRepository.deleteByItineraryId(itineraryId);
    invitationRepository.deleteByItineraryId(itineraryId);
    memberRepository.deleteByItineraryId(itineraryId);
    itineraryRepository.delete(itinerary);

    log.info("[deleteItinerary] <<< Output: itinerary {} deleted successfully", itineraryId);
  }

}
