package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.constraints.NotBlank;

public class InvitationActionRequest {

  // "ACCEPTED" or "DECLINED" — validated in the service layer for a clean error message
  @NotBlank(message = "Action is required")
  private String action;

  public InvitationActionRequest() {}

  public InvitationActionRequest(String action) {
    this.action = action;
  }

  public String getAction() { return action; }
  public void setAction(String action) { this.action = action; }

  @Override
  public String toString() {
    return "InvitationActionRequest{action='" + action + "'}";
  }
}
