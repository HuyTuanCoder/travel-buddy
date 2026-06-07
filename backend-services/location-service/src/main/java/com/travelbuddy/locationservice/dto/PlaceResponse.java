package com.travelbuddy.locationservice.dto;

import java.util.UUID;

/**
 * Response shape for place data — used by both REST and (later) gRPC mappings.
 */
public class PlaceResponse {

  private UUID id;
  private String googlePlaceId;
  private String name;
  private String formattedAddress;
  private Double latitude;
  private Double longitude;
  private String photoReference;
  private String placeTypes;

  public PlaceResponse() {}

  public UUID getId() { return id; }
  public void setId(UUID id) { this.id = id; }

  public String getGooglePlaceId() { return googlePlaceId; }
  public void setGooglePlaceId(String googlePlaceId) { this.googlePlaceId = googlePlaceId; }

  public String getName() { return name; }
  public void setName(String name) { this.name = name; }

  public String getFormattedAddress() { return formattedAddress; }
  public void setFormattedAddress(String formattedAddress) { this.formattedAddress = formattedAddress; }

  public Double getLatitude() { return latitude; }
  public void setLatitude(Double latitude) { this.latitude = latitude; }

  public Double getLongitude() { return longitude; }
  public void setLongitude(Double longitude) { this.longitude = longitude; }

  public String getPhotoReference() { return photoReference; }
  public void setPhotoReference(String photoReference) { this.photoReference = photoReference; }

  public String getPlaceTypes() { return placeTypes; }
  public void setPlaceTypes(String placeTypes) { this.placeTypes = placeTypes; }

  @Override
  public String toString() {
    return "PlaceResponse{id=" + id + ", name='" + name + "', googlePlaceId='" + googlePlaceId + "'}";
  }
}
