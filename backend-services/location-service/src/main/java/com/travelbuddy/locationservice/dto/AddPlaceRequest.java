package com.travelbuddy.locationservice.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * Request body for POST /locations — triggers silent hydration of a Google Place.
 */
public class AddPlaceRequest {

  @NotBlank(message = "googlePlaceId is required")
  private String googlePlaceId;

  public AddPlaceRequest() {}

  public String getGooglePlaceId() { return googlePlaceId; }
  public void setGooglePlaceId(String googlePlaceId) { this.googlePlaceId = googlePlaceId; }

  @Override
  public String toString() {
    return "AddPlaceRequest{googlePlaceId='" + googlePlaceId + "'}";
  }
}
