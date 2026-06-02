package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.MemberRole;

import java.time.Instant;
import java.util.UUID;

/**
 * Response shape for pending invitations — used in POST invite response and GET members list.
 */
public class InvitationResponse {

  private UUID id;
  private UUID itineraryId;
  private String userId;
  private MemberRole role;
  private Instant invitedAt;

  public InvitationResponse() {}

  public UUID getId() { return id; }
  public void setId(UUID id) { this.id = id; }

  public UUID getItineraryId() { return itineraryId; }
  public void setItineraryId(UUID itineraryId) { this.itineraryId = itineraryId; }

  public String getUserId() { return userId; }
  public void setUserId(String userId) { this.userId = userId; }

  public MemberRole getRole() { return role; }
  public void setRole(MemberRole role) { this.role = role; }

  public Instant getInvitedAt() { return invitedAt; }
  public void setInvitedAt(Instant invitedAt) { this.invitedAt = invitedAt; }

  @Override
  public String toString() {
    return "InvitationResponse{id=" + id + ", userId='" + userId + "', role=" + role + "}";
  }
}
