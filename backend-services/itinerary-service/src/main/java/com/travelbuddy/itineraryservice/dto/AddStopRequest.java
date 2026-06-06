package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.StopType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;
import java.time.LocalTime;

/**
 * Request to add a new stop onto a specific day.
 * visitOrder is auto-calculated by the service (max + 1 within the day).
 */
public class AddStopRequest {

  @NotBlank(message = "Google Place ID is required")
  private String googlePlaceId;

  @NotNull(message = "Stop type is required")
  private StopType stopType;

  private LocalTime arrivalTime;
  private LocalTime departureTime;
  private BigDecimal estimatedCost;
  private String userNotes;

  public AddStopRequest() {}

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
    return "AddStopRequest{googlePlaceId='" + googlePlaceId + "', stopType=" + stopType + "}";
  }
}
