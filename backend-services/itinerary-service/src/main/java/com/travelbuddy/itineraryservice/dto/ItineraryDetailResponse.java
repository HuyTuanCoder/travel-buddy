package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.ItineraryStatus;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

/**
 * Response shape for GET /itineraries/{id} — the full trip planner view.
 * Nests members, days, and stops so the frontend can render everything in one call.
 */
public class ItineraryDetailResponse {

  private UUID id;
  private String ownerId;
  private String title;
  private ItineraryStatus status;
  private String timezone;
  private Instant createdAt;
  private Instant updatedAt;
  private List<ItineraryMemberResponse> members;
  private List<ItineraryDayResponse> days;

  public ItineraryDetailResponse() {}

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

  public List<ItineraryMemberResponse> getMembers() { return members; }
  public void setMembers(List<ItineraryMemberResponse> members) { this.members = members; }

  public List<ItineraryDayResponse> getDays() { return days; }
  public void setDays(List<ItineraryDayResponse> days) { this.days = days; }

  @Override
  public String toString() {
    return "ItineraryDetailResponse{id=" + id + ", title='" + title + "', members=" +
        (members != null ? members.size() : 0) + ", days=" + (days != null ? days.size() : 0) + "}";
  }
}
