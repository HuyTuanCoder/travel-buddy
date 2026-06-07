package com.travelbuddy.locationservice.repository;

import com.travelbuddy.locationservice.model.Place;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface PlaceRepository extends JpaRepository<Place, UUID> {

  // Used by POST /locations — idempotent check before calling Google
  Optional<Place> findByGooglePlaceId(String googlePlaceId);

  // Used by gRPC GetPlacesBatch — batch lookup for the in-memory merge
  List<Place> findByGooglePlaceIdIn(List<String> googlePlaceIds);
}
