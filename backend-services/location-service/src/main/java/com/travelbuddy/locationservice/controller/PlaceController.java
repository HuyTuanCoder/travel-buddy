package com.travelbuddy.locationservice.controller;

import com.travelbuddy.locationservice.dto.AddPlaceRequest;
import com.travelbuddy.locationservice.dto.PlaceResponse;
import com.travelbuddy.locationservice.mapper.PlaceMapper;
import com.travelbuddy.locationservice.model.Place;
import com.travelbuddy.locationservice.service.PlaceService;
import com.travelbuddy.locationservice.exception.LocationNotFoundException;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/locations")
public class PlaceController {

  private static final Logger log = LoggerFactory.getLogger(PlaceController.class);

  private final PlaceService placeService;
  private final PlaceMapper placeMapper;

  public PlaceController(PlaceService placeService, PlaceMapper placeMapper) {
    this.placeService = placeService;
    this.placeMapper = placeMapper;
  }

  // ==================== POST /locations ====================
  // Silent hydration endpoint — called fire-and-forget by the frontend.
  // Idempotent: safe to call multiple times for the same placeId.

  @PostMapping
  public ResponseEntity<PlaceResponse> addPlace(@Valid @RequestBody AddPlaceRequest request) {
    log.info("[Controller] POST /locations Request: {}", request);

    Place place = placeService.addPlace(request.getGooglePlaceId());
    PlaceResponse response = placeMapper.toResponse(place);

    log.info("[Controller] POST /locations Response: {}", response);
    return ResponseEntity.ok(response);
  }

  // ==================== GET /locations/{googlePlaceId} ====================
  // Simple cache lookup — useful for debugging and frontend direct lookups.

  @GetMapping("/{googlePlaceId}")
  public ResponseEntity<PlaceResponse> getPlace(@PathVariable String googlePlaceId) {
    log.info("[Controller] GET /locations/{} Request", googlePlaceId);

    Place place = placeService.getPlace(googlePlaceId)
        .orElseThrow(() -> new LocationNotFoundException(
            "Location not found in cache for placeId=" + googlePlaceId));

    PlaceResponse response = placeMapper.toResponse(place);
    log.info("[Controller] GET /locations/{} Response: {}", googlePlaceId, response);
    
    return ResponseEntity.ok(response);
  }
}
