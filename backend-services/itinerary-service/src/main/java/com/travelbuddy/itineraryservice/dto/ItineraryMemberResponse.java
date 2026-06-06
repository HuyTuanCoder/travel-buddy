package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.MemberRole;

import java.time.Instant;

/**
 * Nested inside ItineraryDetailResponse — represents one confirmed participant.
 * No status field needed — if they're in this list, they're a member.
 */
public class ItineraryMemberResponse {

  private String userId;
  private MemberRole role;
  private Instant joinedAt;

  public ItineraryMemberResponse() {}

  public String getUserId() { return userId; }
  public void setUserId(String userId) { this.userId = userId; }

  public MemberRole getRole() { return role; }
  public void setRole(MemberRole role) { this.role = role; }

  public Instant getJoinedAt() { return joinedAt; }
  public void setJoinedAt(Instant joinedAt) { this.joinedAt = joinedAt; }

  @Override
  public String toString() {
    return "ItineraryMemberResponse{userId='" + userId + "', role=" + role + "}";
  }
}
