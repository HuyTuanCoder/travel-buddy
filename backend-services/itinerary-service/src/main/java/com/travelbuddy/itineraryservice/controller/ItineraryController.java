package com.travelbuddy.itineraryservice.controller;

import com.travelbuddy.itineraryservice.dto.*;
import com.travelbuddy.itineraryservice.service.ItineraryService;
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
public class ItineraryController {

  private static final Logger log = LoggerFactory.getLogger(ItineraryController.class);

  private final ItineraryService itineraryService;

  public ItineraryController(ItineraryService itineraryService) {
    this.itineraryService = itineraryService;
  }

  // POST /itineraries — create a new trip
  @PostMapping
  public ResponseEntity<ItineraryResponse> createItinerary(
      @Valid @RequestBody CreateItineraryRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] POST /itineraries | userId={}", userId);
    ItineraryResponse response = itineraryService.createItinerary(request, userId);
    return new ResponseEntity<>(response, HttpStatus.CREATED);
  }

  // GET /itineraries — list all trips the current user belongs to
  @GetMapping
  public ResponseEntity<List<ItinerarySummaryResponse>> listItineraries(
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] GET /itineraries | userId={}", userId);
    List<ItinerarySummaryResponse> responses = itineraryService.listItineraries(userId);
    return ResponseEntity.ok(responses);
  }

  // GET /itineraries/{id} — full trip detail with members, days, and stops
  @GetMapping("/{id}")
  public ResponseEntity<ItineraryDetailResponse> getItineraryDetail(
      @PathVariable UUID id,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] GET /itineraries/{} | userId={}", id, userId);
    ItineraryDetailResponse response = itineraryService.getItineraryDetail(id, userId);
    return ResponseEntity.ok(response);
  }

  // PUT /itineraries/{id} — update trip settings (title, timezone, status)
  @PutMapping("/{id}")
  public ResponseEntity<ItineraryResponse> updateItinerary(
      @PathVariable UUID id,
      @Valid @RequestBody UpdateItineraryRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] PUT /itineraries/{} | userId={}", id, userId);
    ItineraryResponse response = itineraryService.updateItinerary(id, request, userId);
    return ResponseEntity.ok(response);
  }

  // DELETE /itineraries/{id} — delete a trip (owner only, cascades everything)
  @DeleteMapping("/{id}")
  public ResponseEntity<Void> deleteItinerary(
      @PathVariable UUID id,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] DELETE /itineraries/{} | userId={}", id, userId);
    itineraryService.deleteItinerary(id, userId);
    return ResponseEntity.noContent().build();
  }
}
