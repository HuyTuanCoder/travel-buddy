package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.MemberRole;
import com.travelbuddy.itineraryservice.model.MemberStatus;

/**
 * Nested inside ItineraryDetailResponse — represents one participant in the trip.
 */
public class ItineraryMemberResponse {

  private String userId;
  private MemberRole role;
  private MemberStatus status;

  public ItineraryMemberResponse() {}

  public String getUserId() { return userId; }
  public void setUserId(String userId) { this.userId = userId; }

  public MemberRole getRole() { return role; }
  public void setRole(MemberRole role) { this.role = role; }

  public MemberStatus getStatus() { return status; }
  public void setStatus(MemberStatus status) { this.status = status; }

  @Override
  public String toString() {
    return "ItineraryMemberResponse{userId='" + userId + "', role=" + role + ", status=" + status + "}";
  }
}
