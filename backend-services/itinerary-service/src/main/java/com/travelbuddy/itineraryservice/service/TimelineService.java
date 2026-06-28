package com.travelbuddy.itineraryservice.service;

import com.travelbuddy.itineraryservice.dto.*;
import com.travelbuddy.itineraryservice.exception.InvalidRequestException;
import com.travelbuddy.itineraryservice.exception.ItineraryNotFoundException;
import com.travelbuddy.itineraryservice.mapper.ItineraryMapper;
import com.travelbuddy.itineraryservice.model.*;
import com.travelbuddy.itineraryservice.repository.ItineraryDayRepository;
import com.travelbuddy.itineraryservice.repository.TripStopRepository;
import com.travelbuddy.itineraryservice.grpc.LocationGrpcClient;
import com.travelbuddy.location.grpc.PlaceInfo;
import jakarta.transaction.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class TimelineService {

  private static final Logger log = LoggerFactory.getLogger(TimelineService.class);

  private final ItineraryDayRepository dayRepository;
  private final TripStopRepository stopRepository;
  private final ItineraryMapper mapper;
  private final AccessGuard accessGuard;
  private final LocationGrpcClient locationGrpcClient;

  public TimelineService(ItineraryDayRepository dayRepository,
                         TripStopRepository stopRepository,
                         ItineraryMapper mapper,
                         AccessGuard accessGuard,
                         LocationGrpcClient locationGrpcClient) {
    this.dayRepository = dayRepository;
    this.stopRepository = stopRepository;
    this.mapper = mapper;
    this.accessGuard = accessGuard;
    this.locationGrpcClient = locationGrpcClient;
  }

  // ==================== POST /itineraries/{id}/days ====================

  @Transactional
  public ItineraryDayResponse addDay(UUID itineraryId, AddDayRequest request, String userId) {
    log.info("[addDay] >>> Input: itineraryId={}, {}, userId={}", itineraryId, request, userId);

    Itinerary itinerary = accessGuard.findItinerary(itineraryId);
    accessGuard.verifyEditPermission(itineraryId, userId);

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
    ItineraryDayResponse response = mapper.toDayResponse(savedDay, Collections.emptyList(), Collections.emptyMap());
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
    accessGuard.verifyEditPermission(itineraryId, userId);

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
    accessGuard.verifyEditPermission(itineraryId, userId);

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
    
    Map<String, PlaceInfo> locationMap = request.getGooglePlaceId() != null ? 
        locationGrpcClient.fetchPlaces(List.of(request.getGooglePlaceId())) : Collections.emptyMap();
    TripStopResponse response = mapper.toStopResponse(savedStop, locationMap);

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
    accessGuard.verifyEditPermission(itineraryId, userId);

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
    
    Map<String, PlaceInfo> locationMap = updatedStop.getGooglePlaceId() != null ? 
        locationGrpcClient.fetchPlaces(List.of(updatedStop.getGooglePlaceId())) : Collections.emptyMap();
    TripStopResponse response = mapper.toStopResponse(updatedStop, locationMap);

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
    accessGuard.verifyEditPermission(itineraryId, userId);

    stopRepository.delete(stop);
    log.info("[removeStop] <<< Output: stop {} deleted", stopId);
  }

  // ==================== PUT /itineraries/stops/{stopId}/move ====================

  @Transactional
  public TripStopResponse moveStop(UUID stopId, MoveStopRequest request, String userId) {
    log.info("[moveStop] >>> Input: stopId={}, targetDayId={}, userId={}", stopId, request.getTargetDayId(), userId);

    TripStop oldStop = stopRepository.findById(stopId)
        .orElseThrow(() -> new ItineraryNotFoundException("Stop not found: " + stopId));

    ItineraryDay targetDay = dayRepository.findById(request.getTargetDayId())
        .orElseThrow(() -> new ItineraryNotFoundException("Target Day not found: " + request.getTargetDayId()));

    UUID itineraryId = oldStop.getItineraryDay().getItinerary().getId();
    UUID targetItineraryId = targetDay.getItinerary().getId();

    if (!itineraryId.equals(targetItineraryId)) {
        throw new InvalidRequestException("Cannot move stops between different itineraries");
    }
    
    accessGuard.verifyEditPermission(itineraryId, userId);

    // Calculate visit order for new day
    int nextVisitOrder = stopRepository.findMaxVisitOrderByDayId(request.getTargetDayId())
        .map(max -> max + 1)
        .orElse(1);
        
    int finalVisitOrder = request.getTargetVisitOrder() != null ? request.getTargetVisitOrder() : nextVisitOrder;

    // Create a new stop instance because itineraryDay is not updatable
    TripStop newStop = new TripStop();
    newStop.setItineraryDay(targetDay);
    newStop.setGooglePlaceId(oldStop.getGooglePlaceId());
    newStop.setStopType(oldStop.getStopType());
    newStop.setVisitOrder(finalVisitOrder);
    newStop.setArrivalTime(oldStop.getArrivalTime());
    newStop.setDepartureTime(oldStop.getDepartureTime());
    newStop.setEstimatedCost(oldStop.getEstimatedCost());
    newStop.setUserNotes(oldStop.getUserNotes());

    // Save the new stop and delete the old one transactionally
    TripStop savedStop = stopRepository.save(newStop);
    stopRepository.delete(oldStop);
    
    // Optional: If targetVisitOrder was provided, we may need to shift existing stops down.
    // For now, since the AI handles ordering cleanly, we can just save it. 
    // Wait, let's just do a simple shift if needed. 
    if (request.getTargetVisitOrder() != null) {
        List<TripStop> otherStops = stopRepository.findByItineraryDayIdOrderByVisitOrderAsc(targetDay.getId());
        int currentOrder = 0;
        for (TripStop other : otherStops) {
            if (!other.getId().equals(savedStop.getId())) {
                if (currentOrder == finalVisitOrder) currentOrder++;
                other.setVisitOrder(currentOrder++);
                stopRepository.save(other);
            }
        }
    }

    Map<String, PlaceInfo> locationMap = savedStop.getGooglePlaceId() != null ? 
        locationGrpcClient.fetchPlaces(List.of(savedStop.getGooglePlaceId())) : Collections.emptyMap();
    TripStopResponse response = mapper.toStopResponse(savedStop, locationMap);

    log.info("[moveStop] <<< Output: {}", response);
    return response;
  }

  // ==================== PUT /itineraries/days/{dayId}/stops/reorder ====================

  @Transactional
  public List<TripStopResponse> reorderStops(UUID dayId, ReorderStopsRequest request, String userId) {
    log.info("[reorderStops] >>> Input: dayId={}, {}, userId={}", dayId, request, userId);

    ItineraryDay day = dayRepository.findById(dayId)
        .orElseThrow(() -> new ItineraryNotFoundException("Day not found: " + dayId));

    UUID itineraryId = day.getItinerary().getId();
    accessGuard.verifyEditPermission(itineraryId, userId);

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

    // Fetch location data for all reordered stops
    List<String> googlePlaceIds = savedStops.stream()
        .map(TripStop::getGooglePlaceId)
        .filter(id -> id != null && !id.isEmpty())
        .distinct()
        .collect(Collectors.toList());
    Map<String, PlaceInfo> locationMap = locationGrpcClient.fetchPlaces(googlePlaceIds);

    // Return in the new order
    List<TripStopResponse> responses = savedStops.stream()
        .sorted((a, b) -> a.getVisitOrder().compareTo(b.getVisitOrder()))
        .map(stop -> mapper.toStopResponse(stop, locationMap))
        .collect(Collectors.toList());

    log.info("[reorderStops] <<< Output: {} stops reordered", responses.size());
    return responses;
  }

  // ==================== PUT /itineraries/{id}/days/swap ====================

  @Transactional
  public void swapDays(UUID itineraryId, SwapDaysRequest request, String userId) {
    log.info("[swapDays] >>> Input: itineraryId={}, dayA={}, dayB={}, userId={}", itineraryId, request.getDayA(), request.getDayB(), userId);

    accessGuard.verifyEditPermission(itineraryId, userId);

    List<ItineraryDay> days = dayRepository.findByItineraryIdOrderByDayNumberAsc(itineraryId);
    
    ItineraryDay day1 = days.stream().filter(d -> d.getDayNumber().equals(request.getDayA())).findFirst()
        .orElseThrow(() -> new InvalidRequestException("Day number not found: " + request.getDayA()));
        
    ItineraryDay day2 = days.stream().filter(d -> d.getDayNumber().equals(request.getDayB())).findFirst()
        .orElseThrow(() -> new InvalidRequestException("Day number not found: " + request.getDayB()));

    Integer temp = day1.getDayNumber();
    day1.setDayNumber(day2.getDayNumber());
    day2.setDayNumber(temp);

    dayRepository.saveAll(List.of(day1, day2));
    
    log.info("[swapDays] <<< Output: day {} and day {} swapped", request.getDayA(), request.getDayB());
  }
}
