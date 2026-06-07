package com.travelbuddy.locationservice.service;

import com.travelbuddy.locationservice.client.GooglePlacesClient;
import com.travelbuddy.locationservice.model.Place;
import com.travelbuddy.locationservice.repository.PlaceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class PlaceService {

  private static final Logger log = LoggerFactory.getLogger(PlaceService.class);

  private final PlaceRepository placeRepository;
  private final GooglePlacesClient googlePlacesClient;

  public PlaceService(PlaceRepository placeRepository, GooglePlacesClient googlePlacesClient) {
    this.placeRepository = placeRepository;
    this.googlePlacesClient = googlePlacesClient;
  }

  // ==================== POST /locations ====================

  /**
   * Adds a place to the local cache. Idempotent — if the place already exists,
   * we return the cached version without hitting Google again.
   */
  public Place addPlace(String googlePlaceId) {
    log.info("[addPlace] >>> Input: googlePlaceId={}", googlePlaceId);

    // 1. Check if we already have this place cached
    Optional<Place> existing = placeRepository.findByGooglePlaceId(googlePlaceId);
    if (existing.isPresent()) {
      log.info("[addPlace] <<< Cache hit — returning existing place");
      return existing.get();
    }

    // 2. Cache miss — fetch from Google Maps
    GooglePlacesClient.PlaceDetailsResult details = googlePlacesClient.fetchPlaceDetails(googlePlaceId);

    // 3. Map to entity and persist
    Place place = new Place();
    place.setGooglePlaceId(googlePlaceId);
    place.setName(details.getName());
    place.setFormattedAddress(details.getFormattedAddress());
    place.setLatitude(details.getLatitude());
    place.setLongitude(details.getLongitude());
    place.setPhotoReference(details.getPhotoReference());
    place.setPlaceTypes(details.getPlaceTypes());

    Place savedPlace = placeRepository.save(place);
    log.info("[addPlace] <<< Saved new place: {}", savedPlace.getName());
    return savedPlace;
  }

  // ==================== GET /locations/{googlePlaceId} ====================

  /**
   * Simple cache lookup. Returns empty if the place hasn't been hydrated yet.
   */
  public Optional<Place> getPlace(String googlePlaceId) {
    log.info("[getPlace] >>> Input: googlePlaceId={}", googlePlaceId);
    return placeRepository.findByGooglePlaceId(googlePlaceId);
  }

  // ==================== Batch Lookup (for future gRPC) ====================

  /**
   * Fetches multiple places by their Google Place IDs.
   * Self-healing: any IDs not in the cache are fetched from Google on-demand.
   */
  public List<Place> getPlacesBatch(List<String> googlePlaceIds) {
    log.info("[getPlacesBatch] >>> Input: {} place IDs", googlePlaceIds.size());

    if (googlePlaceIds.isEmpty()) {
      return Collections.emptyList();
    }

    // 1. Batch lookup from the database
    List<Place> cached = placeRepository.findByGooglePlaceIdIn(googlePlaceIds);
    Set<String> cachedIds = cached.stream()
        .map(Place::getGooglePlaceId)
        .collect(Collectors.toSet());

    // 2. Find which IDs are missing from the cache
    List<String> missingIds = googlePlaceIds.stream()
        .filter(id -> !cachedIds.contains(id))
        .collect(Collectors.toList());

    // 3. Fetch and save any missing places (self-healing)
    if (!missingIds.isEmpty()) {
      log.info("[getPlacesBatch] Cache misses: {} — fetching from Google", missingIds.size());
      for (String missingId : missingIds) {
        try {
          Place filled = addPlace(missingId);
          cached.add(filled);
        } catch (Exception e) {
          log.warn("[getPlacesBatch] Failed to fetch placeId={}: {}", missingId, e.getMessage());
          // Skip this place — graceful degradation
        }
      }
    }

    log.info("[getPlacesBatch] <<< Returning {} places", cached.size());
    return cached;
  }
}
