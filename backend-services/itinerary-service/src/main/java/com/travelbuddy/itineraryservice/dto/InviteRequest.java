package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.MemberRole;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class InviteRequest {

  @NotBlank(message = "Invitee user ID is required")
  private String inviteeUserId;

  @NotNull(message = "Role is required")
  private MemberRole role;

  public InviteRequest() {}

  public InviteRequest(String inviteeUserId, MemberRole role) {
    this.inviteeUserId = inviteeUserId;
    this.role = role;
  }

  public String getInviteeUserId() { return inviteeUserId; }
  public void setInviteeUserId(String inviteeUserId) { this.inviteeUserId = inviteeUserId; }

  public MemberRole getRole() { return role; }
  public void setRole(MemberRole role) { this.role = role; }

  @Override
  public String toString() {
    return "InviteRequest{inviteeUserId='" + inviteeUserId + "', role=" + role + "}";
  }
}
