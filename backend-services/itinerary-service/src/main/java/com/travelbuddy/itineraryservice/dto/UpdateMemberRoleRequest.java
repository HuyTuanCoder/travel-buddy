package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.MemberRole;
import jakarta.validation.constraints.NotNull;

public class UpdateMemberRoleRequest {

  @NotNull(message = "Role is required")
  private MemberRole role;

  public UpdateMemberRoleRequest() {}

  public UpdateMemberRoleRequest(MemberRole role) {
    this.role = role;
  }

  public MemberRole getRole() { return role; }
  public void setRole(MemberRole role) { this.role = role; }

  @Override
  public String toString() {
    return "UpdateMemberRoleRequest{role=" + role + "}";
  }
}
