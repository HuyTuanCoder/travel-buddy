package com.travelbuddy.itineraryservice.dto;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

/**
 * Nested inside ItineraryDetailResponse — represents one day in the trip timeline.
 * Contains its own list of stops, sorted by visitOrder.
 */
public class ItineraryDayResponse {

  private UUID id;
  private Integer dayNumber;
  private LocalDate scheduledDate;
  private List<TripStopResponse> stops;

  public ItineraryDayResponse() {}

  public UUID getId() { return id; }
  public void setId(UUID id) { this.id = id; }

  public Integer getDayNumber() { return dayNumber; }
  public void setDayNumber(Integer dayNumber) { this.dayNumber = dayNumber; }

  public LocalDate getScheduledDate() { return scheduledDate; }
  public void setScheduledDate(LocalDate scheduledDate) { this.scheduledDate = scheduledDate; }

  public List<TripStopResponse> getStops() { return stops; }
  public void setStops(List<TripStopResponse> stops) { this.stops = stops; }

  @Override
  public String toString() {
    return "ItineraryDayResponse{id=" + id + ", dayNumber=" + dayNumber +
        ", stops=" + (stops != null ? stops.size() : 0) + "}";
  }
}
