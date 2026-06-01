package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.ItineraryStatus;
import com.travelbuddy.itineraryservice.model.MemberRole;

import java.time.Instant;
import java.util.UUID;

/**
 * Response shape for GET /itineraries — the trip card in the list view.
 * Includes the current user's role so the frontend knows what UI controls to show.
 */
public class ItinerarySummaryResponse {

  private UUID id;
  private String title;
  private ItineraryStatus status;
  private String timezone;
  private MemberRole role;
  private Instant createdAt;

  public ItinerarySummaryResponse() {}

  public UUID getId() { return id; }
  public void setId(UUID id) { this.id = id; }

  public String getTitle() { return title; }
  public void setTitle(String title) { this.title = title; }

  public ItineraryStatus getStatus() { return status; }
  public void setStatus(ItineraryStatus status) { this.status = status; }

  public String getTimezone() { return timezone; }
  public void setTimezone(String timezone) { this.timezone = timezone; }

  public MemberRole getRole() { return role; }
  public void setRole(MemberRole role) { this.role = role; }

  public Instant getCreatedAt() { return createdAt; }
  public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

  @Override
  public String toString() {
    return "ItinerarySummaryResponse{id=" + id + ", title='" + title + "', role=" + role + "}";
  }
}
