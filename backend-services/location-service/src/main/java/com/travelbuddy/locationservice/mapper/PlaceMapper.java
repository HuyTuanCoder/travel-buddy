package com.travelbuddy.locationservice.mapper;

import com.travelbuddy.locationservice.dto.PlaceResponse;
import com.travelbuddy.locationservice.model.Place;
import org.springframework.stereotype.Component;

@Component
public class PlaceMapper {

  // --- Entity → Response ---

  public PlaceResponse toResponse(Place place) {
    PlaceResponse response = new PlaceResponse();
    response.setId(place.getId());
    response.setGooglePlaceId(place.getGooglePlaceId());
    response.setName(place.getName());
    response.setFormattedAddress(place.getFormattedAddress());
    response.setLatitude(place.getLatitude());
    response.setLongitude(place.getLongitude());
    response.setPhotoReference(place.getPhotoReference());
    response.setPlaceTypes(place.getPlaceTypes());
    return response;
  }
}
