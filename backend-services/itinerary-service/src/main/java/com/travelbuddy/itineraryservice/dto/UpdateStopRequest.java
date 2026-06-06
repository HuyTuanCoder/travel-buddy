package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.StopType;

import java.math.BigDecimal;
import java.time.LocalTime;

/**
 * Partial update request for an existing stop.
 * All fields are nullable — only non-null fields are applied (PATCH semantics on a PUT).
 */
public class UpdateStopRequest {

  private String googlePlaceId;
  private StopType stopType;
  private LocalTime arrivalTime;
  private LocalTime departureTime;
  private BigDecimal estimatedCost;
  private String userNotes;

  public UpdateStopRequest() {}

  public String getGooglePlaceId() { return googlePlaceId; }
  public void setGooglePlaceId(String googlePlaceId) { this.googlePlaceId = googlePlaceId; }

  public StopType getStopType() { return stopType; }
  public void setStopType(StopType stopType) { this.stopType = stopType; }

  public LocalTime getArrivalTime() { return arrivalTime; }
  public void setArrivalTime(LocalTime arrivalTime) { this.arrivalTime = arrivalTime; }

  public LocalTime getDepartureTime() { return departureTime; }
  public void setDepartureTime(LocalTime departureTime) { this.departureTime = departureTime; }

  public BigDecimal getEstimatedCost() { return estimatedCost; }
  public void setEstimatedCost(BigDecimal estimatedCost) { this.estimatedCost = estimatedCost; }

  public String getUserNotes() { return userNotes; }
  public void setUserNotes(String userNotes) { this.userNotes = userNotes; }

  @Override
  public String toString() {
    return "UpdateStopRequest{googlePlaceId='" + googlePlaceId + "', stopType=" + stopType + "}";
  }
}
