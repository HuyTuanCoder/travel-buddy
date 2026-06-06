package com.travelbuddy.itineraryservice.service;

import com.travelbuddy.itineraryservice.dto.*;
import com.travelbuddy.itineraryservice.exception.AccessDeniedException;
import com.travelbuddy.itineraryservice.exception.InvalidRequestException;
import com.travelbuddy.itineraryservice.exception.ItineraryNotFoundException;
import com.travelbuddy.itineraryservice.mapper.ItineraryMapper;
import com.travelbuddy.itineraryservice.model.*;
import com.travelbuddy.itineraryservice.repository.ItineraryDayRepository;
import com.travelbuddy.itineraryservice.repository.ItineraryMemberRepository;
import com.travelbuddy.itineraryservice.repository.ItineraryRepository;
import com.travelbuddy.itineraryservice.repository.TripStopRepository;
import jakarta.transaction.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class TimelineService {

  private static final Logger log = LoggerFactory.getLogger(TimelineService.class);

  private final ItineraryRepository itineraryRepository;
  private final ItineraryMemberRepository memberRepository;
  private final ItineraryDayRepository dayRepository;
  private final TripStopRepository stopRepository;
  private final ItineraryMapper mapper;

  public TimelineService(ItineraryRepository itineraryRepository,
                         ItineraryMemberRepository memberRepository,
                         ItineraryDayRepository dayRepository,
                         TripStopRepository stopRepository,
                         ItineraryMapper mapper) {
    this.itineraryRepository = itineraryRepository;
    this.memberRepository = memberRepository;
    this.dayRepository = dayRepository;
    this.stopRepository = stopRepository;
    this.mapper = mapper;
  }

  // ==================== POST /itineraries/{id}/days ====================

  @Transactional
  public ItineraryDayResponse addDay(UUID itineraryId, AddDayRequest request, String userId) {
    log.info("[addDay] >>> Input: itineraryId={}, {}, userId={}", itineraryId, request, userId);

    Itinerary itinerary = findItinerary(itineraryId);
    verifyEditPermission(itineraryId, userId);

    // Auto-calculate the next day number (max + 1, or 1 if no days exist)
    int nextDayNumber = dayRepository.findMaxDayNumberByItineraryId(itineraryId)
        .map(max -> max + 1)
        .orElse(1);

    ItineraryDay day = new ItineraryDay();
    day.setItinerary(itinerary);
    day.setDayNumber(nextDayNumber);
    day.setScheduledDate(request.getScheduledDate());

    ItineraryDay savedDay = dayRepository.save(day);

    // Return with an empty stops list — it was just created
    ItineraryDayResponse response = mapper.toDayResponse(savedDay, Collections.emptyList());
    log.info("[addDay] <<< Output: {}", response);
    return response;
  }

  // ==================== DELETE /itineraries/days/{dayId} ====================

  @Transactional
  public void removeDay(UUID dayId, String userId) {
    log.info("[removeDay] >>> Input: dayId={}, userId={}", dayId, userId);

    ItineraryDay day = dayRepository.findById(dayId)
        .orElseThrow(() -> new ItineraryNotFoundException("Day not found: " + dayId));

    UUID itineraryId = day.getItinerary().getId();
    verifyEditPermission(itineraryId, userId);

    // Cascade: delete all stops on this day first, then the day itself
    stopRepository.deleteByDayId(dayId);
    dayRepository.delete(day);

    log.info("[removeDay] <<< Output: day {} deleted, stops cascade-deleted", dayId);
  }

  // ==================== POST /itineraries/days/{dayId}/stops ====================

  @Transactional
  public TripStopResponse addStop(UUID dayId, AddStopRequest request, String userId) {
    log.info("[addStop] >>> Input: dayId={}, {}, userId={}", dayId, request, userId);

    ItineraryDay day = dayRepository.findById(dayId)
        .orElseThrow(() -> new ItineraryNotFoundException("Day not found: " + dayId));

    UUID itineraryId = day.getItinerary().getId();
    verifyEditPermission(itineraryId, userId);

    // Auto-calculate the next visit order within this day
    int nextVisitOrder = stopRepository.findMaxVisitOrderByDayId(dayId)
        .map(max -> max + 1)
        .orElse(1);

    TripStop stop = new TripStop();
    stop.setItineraryDay(day);
    stop.setGooglePlaceId(request.getGooglePlaceId());
    stop.setStopType(request.getStopType());
    stop.setVisitOrder(nextVisitOrder);
    stop.setArrivalTime(request.getArrivalTime());
    stop.setDepartureTime(request.getDepartureTime());
    stop.setEstimatedCost(request.getEstimatedCost());
    stop.setUserNotes(request.getUserNotes());

    TripStop savedStop = stopRepository.save(stop);
    TripStopResponse response = mapper.toStopResponse(savedStop);

    log.info("[addStop] <<< Output: {}", response);
    return response;
  }

  // ==================== PUT /itineraries/stops/{stopId} ====================

  @Transactional
  public TripStopResponse updateStop(UUID stopId, UpdateStopRequest request, String userId) {
    log.info("[updateStop] >>> Input: stopId={}, {}, userId={}", stopId, request, userId);

    TripStop stop = stopRepository.findById(stopId)
        .orElseThrow(() -> new ItineraryNotFoundException("Stop not found: " + stopId));

    UUID itineraryId = stop.getItineraryDay().getItinerary().getId();
    verifyEditPermission(itineraryId, userId);

    // Apply only non-null fields (partial update)
    if (request.getGooglePlaceId() != null) {
      stop.setGooglePlaceId(request.getGooglePlaceId());
    }
    if (request.getStopType() != null) {
      stop.setStopType(request.getStopType());
    }
    if (request.getArrivalTime() != null) {
      stop.setArrivalTime(request.getArrivalTime());
    }
    if (request.getDepartureTime() != null) {
      stop.setDepartureTime(request.getDepartureTime());
    }
    if (request.getEstimatedCost() != null) {
      stop.setEstimatedCost(request.getEstimatedCost());
    }
    if (request.getUserNotes() != null) {
      stop.setUserNotes(request.getUserNotes());
    }

    TripStop updatedStop = stopRepository.save(stop);
    TripStopResponse response = mapper.toStopResponse(updatedStop);

    log.info("[updateStop] <<< Output: {}", response);
    return response;
  }

  // ==================== DELETE /itineraries/stops/{stopId} ====================

  @Transactional
  public void removeStop(UUID stopId, String userId) {
    log.info("[removeStop] >>> Input: stopId={}, userId={}", stopId, userId);

    TripStop stop = stopRepository.findById(stopId)
        .orElseThrow(() -> new ItineraryNotFoundException("Stop not found: " + stopId));

    UUID itineraryId = stop.getItineraryDay().getItinerary().getId();
    verifyEditPermission(itineraryId, userId);

    stopRepository.delete(stop);
    log.info("[removeStop] <<< Output: stop {} deleted", stopId);
  }

  // ==================== PUT /itineraries/days/{dayId}/stops/reorder ====================

  @Transactional
  public List<TripStopResponse> reorderStops(UUID dayId, ReorderStopsRequest request, String userId) {
    log.info("[reorderStops] >>> Input: dayId={}, {}, userId={}", dayId, request, userId);

    ItineraryDay day = dayRepository.findById(dayId)
        .orElseThrow(() -> new ItineraryNotFoundException("Day not found: " + dayId));

    UUID itineraryId = day.getItinerary().getId();
    verifyEditPermission(itineraryId, userId);

    // Fetch all existing stops for this day to validate the incoming list
    List<TripStop> existingStops = stopRepository.findByItineraryDayIdOrderByVisitOrderAsc(dayId);
    List<UUID> existingIds = existingStops.stream()
        .map(TripStop::getId)
        .collect(Collectors.toList());

    // Validate: the incoming list must contain exactly the same stop IDs (no extras, no missing)
    if (request.getStopIds().size() != existingIds.size()
        || !request.getStopIds().containsAll(existingIds)) {
      throw new InvalidRequestException(
          "Stop IDs must contain exactly all stops for this day. Expected " + existingIds.size()
              + " stops, got " + request.getStopIds().size());
    }

    // Assign visitOrder based on the new list index (1-based)
    for (int i = 0; i < request.getStopIds().size(); i++) {
      UUID stopId = request.getStopIds().get(i);
      TripStop stop = existingStops.stream()
          .filter(s -> s.getId().equals(stopId))
          .findFirst()
          .orElseThrow(() -> new InvalidRequestException("Stop ID not found in this day: " + stopId));
      stop.setVisitOrder(i + 1);
    }

    // Batch save all updated stops
    List<TripStop> savedStops = stopRepository.saveAll(existingStops);

    // Return in the new order
    List<TripStopResponse> responses = savedStops.stream()
        .sorted((a, b) -> a.getVisitOrder().compareTo(b.getVisitOrder()))
        .map(mapper::toStopResponse)
        .collect(Collectors.toList());

    log.info("[reorderStops] <<< Output: {} stops reordered", responses.size());
    return responses;
  }

  // ==================== RBAC Helpers ====================

  private Itinerary findItinerary(UUID itineraryId) {
    return itineraryRepository.findById(itineraryId)
        .orElseThrow(() -> new ItineraryNotFoundException("Itinerary not found: " + itineraryId));
  }

  // Verifies the user is OWNER or EDITOR — both day and stop operations require edit permission
  private void verifyEditPermission(UUID itineraryId, String userId) {
    ItineraryMember member = memberRepository.findByItineraryIdAndUserId(itineraryId, userId)
        .orElseThrow(() -> new AccessDeniedException(
            "User " + userId + " is not a member of itinerary " + itineraryId));

    if (member.getRole() != MemberRole.OWNER && member.getRole() != MemberRole.EDITOR) {
      throw new AccessDeniedException(
          "User " + userId + " does not have edit permission on itinerary " + itineraryId);
    }
  }
}
