package com.travelbuddy.itineraryservice.controller;

import com.travelbuddy.itineraryservice.dto.*;
import com.travelbuddy.itineraryservice.service.TimelineService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/itineraries")
public class TimelineController {

  private static final Logger log = LoggerFactory.getLogger(TimelineController.class);

  private final TimelineService timelineService;

  public TimelineController(TimelineService timelineService) {
    this.timelineService = timelineService;
  }

  // ==================== Day Endpoints ====================

  // POST /itineraries/{id}/days — append a new day to the trip
  @PostMapping("/{id}/days")
  public ResponseEntity<ItineraryDayResponse> addDay(
      @PathVariable UUID id,
      @RequestBody AddDayRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] POST /itineraries/{}/days | userId={}", id, userId);
    ItineraryDayResponse response = timelineService.addDay(id, request, userId);
    return new ResponseEntity<>(response, HttpStatus.CREATED);
  }

  // DELETE /itineraries/days/{dayId} — remove a day and cascade-delete its stops
  @DeleteMapping("/days/{dayId}")
  public ResponseEntity<Void> removeDay(
      @PathVariable UUID dayId,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] DELETE /itineraries/days/{} | userId={}", dayId, userId);
    timelineService.removeDay(dayId, userId);
    return ResponseEntity.noContent().build();
  }

  // ==================== Stop Endpoints ====================

  // POST /itineraries/days/{dayId}/stops — add a stop to a specific day
  @PostMapping("/days/{dayId}/stops")
  public ResponseEntity<TripStopResponse> addStop(
      @PathVariable UUID dayId,
      @Valid @RequestBody AddStopRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] POST /itineraries/days/{}/stops | userId={}", dayId, userId);
    TripStopResponse response = timelineService.addStop(dayId, request, userId);
    return new ResponseEntity<>(response, HttpStatus.CREATED);
  }

  // PUT /itineraries/stops/{stopId} — update a stop's details
  @PutMapping("/stops/{stopId}")
  public ResponseEntity<TripStopResponse> updateStop(
      @PathVariable UUID stopId,
      @RequestBody UpdateStopRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] PUT /itineraries/stops/{} | userId={}", stopId, userId);
    TripStopResponse response = timelineService.updateStop(stopId, request, userId);
    return ResponseEntity.ok(response);
  }

  // DELETE /itineraries/stops/{stopId} — remove a stop
  @DeleteMapping("/stops/{stopId}")
  public ResponseEntity<Void> removeStop(
      @PathVariable UUID stopId,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] DELETE /itineraries/stops/{} | userId={}", stopId, userId);
    timelineService.removeStop(stopId, userId);
    return ResponseEntity.noContent().build();
  }

  // PUT /itineraries/days/{dayId}/stops/reorder — drag-and-drop reorder
  @PutMapping("/days/{dayId}/stops/reorder")
  public ResponseEntity<List<TripStopResponse>> reorderStops(
      @PathVariable UUID dayId,
      @Valid @RequestBody ReorderStopsRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] PUT /itineraries/days/{}/stops/reorder | userId={}", dayId, userId);
    List<TripStopResponse> responses = timelineService.reorderStops(dayId, request, userId);
    return ResponseEntity.ok(responses);
  }

  // PUT /itineraries/stops/{stopId}/move — move a stop across days or within a day
  @PutMapping("/stops/{stopId}/move")
  public ResponseEntity<TripStopResponse> moveStop(
      @PathVariable UUID stopId,
      @Valid @RequestBody MoveStopRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] PUT /itineraries/stops/{}/move | userId={}", stopId, userId);
    TripStopResponse response = timelineService.moveStop(stopId, request, userId);
    return ResponseEntity.ok(response);
  }
}
