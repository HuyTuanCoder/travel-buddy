package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.ItineraryStatus;

import java.time.Instant;
import java.util.UUID;

/**
 * Response shape for POST and PUT /itineraries — just the itinerary metadata.
 * Used when the frontend already has days/stops loaded and only needs the updated header.
 */
public class ItineraryResponse {

  private UUID id;
  private String ownerId;
  private String title;
  private ItineraryStatus status;
  private String timezone;
  private Instant createdAt;
  private Instant updatedAt;

  public ItineraryResponse() {}

  public UUID getId() { return id; }
  public void setId(UUID id) { this.id = id; }

  public String getOwnerId() { return ownerId; }
  public void setOwnerId(String ownerId) { this.ownerId = ownerId; }

  public String getTitle() { return title; }
  public void setTitle(String title) { this.title = title; }

  public ItineraryStatus getStatus() { return status; }
  public void setStatus(ItineraryStatus status) { this.status = status; }

  public String getTimezone() { return timezone; }
  public void setTimezone(String timezone) { this.timezone = timezone; }

  public Instant getCreatedAt() { return createdAt; }
  public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

  public Instant getUpdatedAt() { return updatedAt; }
  public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }

  @Override
  public String toString() {
    return "ItineraryResponse{id=" + id + ", title='" + title + "', status=" + status + "}";
  }
}
