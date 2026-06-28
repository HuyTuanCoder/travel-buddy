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

    Itinerary itinerary = accessGuard.findItinerary(itineraryId);
    accessGuard.verifyEditPermission(itineraryId, userId);

    List<ItineraryDay> existingDays = dayRepository.findByItineraryIdOrderByDayNumberAsc(itineraryId);
    Map<UUID, ItineraryDay> dayMap = existingDays.stream()
        .collect(Collectors.toMap(ItineraryDay::getId, day -> day));

    // 1. Gather all incoming day UUIDs
    List<UUID> incomingDayIds = request.getDays().stream()
        .map(req -> {
            try { return UUID.fromString(req.getId()); }
            catch (Exception e) { return null; }
        })
        .filter(id -> id != null)
        .collect(Collectors.toList());

    // 2. Delete existing days not in payload
    for (ItineraryDay existingDay : existingDays) {
        if (!incomingDayIds.contains(existingDay.getId())) {
            dayRepository.delete(existingDay);
        }
    }

    // 3. Process incoming days
    Map<String, ItineraryDay> processedDays = new java.util.HashMap<>();
    
    for (int i = 0; i < request.getDays().size(); i++) {
        BatchUpdateDayRequest dayReq = request.getDays().get(i);
        UUID dayId = null;
        try { dayId = UUID.fromString(dayReq.getId()); }
        catch (Exception e) { }
        
        ItineraryDay dayToSave;
        if (dayId != null && dayMap.containsKey(dayId)) {
            dayToSave = dayMap.get(dayId);
        } else {
            dayToSave = new ItineraryDay();
            dayToSave.setItinerary(itinerary);
        }
        
        // Use provided dayNumber, fallback to index + 1
        int dayNumber = dayReq.getDayNumber() != null ? dayReq.getDayNumber() : (i + 1);
        dayToSave.setDayNumber(dayNumber);
        dayToSave = dayRepository.save(dayToSave);
        processedDays.put(dayReq.getId(), dayToSave);
    }
    
    // 4. Gather all valid incoming stop UUIDs across ALL days
    List<UUID> incomingStopIds = new java.util.ArrayList<>();
    for (BatchUpdateDayRequest dayReq : request.getDays()) {
        for (BatchUpdateStopRequest stopReq : dayReq.getStops()) {
            try { incomingStopIds.add(UUID.fromString(stopReq.getId())); }
            catch (Exception e) { }
        }
    }
    
    // 5. Delete existing stops not in payload anywhere
    // Fetch remaining days from DB just to be safe
    List<ItineraryDay> remainingDays = dayRepository.findByItineraryIdOrderByDayNumberAsc(itineraryId);
    for (ItineraryDay d : remainingDays) {
        List<TripStop> dayStops = stopRepository.findByItineraryDayIdOrderByVisitOrderAsc(d.getId());
        for (TripStop stop : dayStops) {
            if (!incomingStopIds.contains(stop.getId())) {
                stopRepository.delete(stop);
            }
        }
    }

    // 6. Process incoming stops
    for (BatchUpdateDayRequest dayReq : request.getDays()) {
        ItineraryDay day = processedDays.get(dayReq.getId());
        if (day == null) continue;
        
        // We load existing stops for this day in case we need to update them
        List<TripStop> existingStops = stopRepository.findByItineraryDayIdOrderByVisitOrderAsc(day.getId());
        Map<UUID, TripStop> existingStopMap = existingStops.stream()
            .collect(Collectors.toMap(TripStop::getId, stop -> stop));
            
        int visitOrder = 0;
        for (BatchUpdateStopRequest stopReq : dayReq.getStops()) {
            UUID stopId = null;
            try { stopId = UUID.fromString(stopReq.getId()); }
            catch (Exception e) { }
            
            TripStop stopToSave;
            if (stopId != null && existingStopMap.containsKey(stopId)) {
                stopToSave = existingStopMap.get(stopId);
            } else if (stopId != null) {
                // Stop might have been moved from another day! We need to fetch it globally.
                stopToSave = stopRepository.findById(stopId).orElse(new TripStop());
            } else {
                stopToSave = new TripStop();
            }
            
            stopToSave.setItineraryDay(day); // Re-parent if moved
            
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
