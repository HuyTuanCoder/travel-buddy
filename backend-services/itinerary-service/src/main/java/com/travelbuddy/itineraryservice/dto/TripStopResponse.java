package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.StopType;

import java.math.BigDecimal;
import java.time.LocalTime;
import java.util.UUID;

/**
 * Nested inside ItineraryDayResponse — represents one stop/event within a day.
 */
public class TripStopResponse {

  private UUID id;
  private String googlePlaceId;
  private Integer visitOrder;
  private LocalTime arrivalTime;
  private LocalTime departureTime;
  private StopType stopType;
  private BigDecimal estimatedCost;
  private String userNotes;

  public TripStopResponse() {}

  public UUID getId() { return id; }
  public void setId(UUID id) { this.id = id; }

  public String getGooglePlaceId() { return googlePlaceId; }
  public void setGooglePlaceId(String googlePlaceId) { this.googlePlaceId = googlePlaceId; }

  public Integer getVisitOrder() { return visitOrder; }
  public void setVisitOrder(Integer visitOrder) { this.visitOrder = visitOrder; }

  public LocalTime getArrivalTime() { return arrivalTime; }
  public void setArrivalTime(LocalTime arrivalTime) { this.arrivalTime = arrivalTime; }

  public LocalTime getDepartureTime() { return departureTime; }
  public void setDepartureTime(LocalTime departureTime) { this.departureTime = departureTime; }

  public StopType getStopType() { return stopType; }
  public void setStopType(StopType stopType) { this.stopType = stopType; }

  public BigDecimal getEstimatedCost() { return estimatedCost; }
  public void setEstimatedCost(BigDecimal estimatedCost) { this.estimatedCost = estimatedCost; }

  public String getUserNotes() { return userNotes; }
  public void setUserNotes(String userNotes) { this.userNotes = userNotes; }

  @Override
  public String toString() {
    return "TripStopResponse{id=" + id + ", stopType=" + stopType + ", visitOrder=" + visitOrder + "}";
  }
}
