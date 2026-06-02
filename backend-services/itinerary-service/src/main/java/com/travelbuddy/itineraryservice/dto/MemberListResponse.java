package com.travelbuddy.itineraryservice.dto;

import java.util.List;

/**
 * Response shape for GET /itineraries/{id}/members.
 * Cleanly separates confirmed members from pending invitations — no ambiguous status enums.
 */
public class MemberListResponse {

  private List<ItineraryMemberResponse> members;
  private List<InvitationResponse> pendingInvitations;

  public MemberListResponse() {}

  public MemberListResponse(List<ItineraryMemberResponse> members, List<InvitationResponse> pendingInvitations) {
    this.members = members;
    this.pendingInvitations = pendingInvitations;
  }

  public List<ItineraryMemberResponse> getMembers() { return members; }
  public void setMembers(List<ItineraryMemberResponse> members) { this.members = members; }

  public List<InvitationResponse> getPendingInvitations() { return pendingInvitations; }
  public void setPendingInvitations(List<InvitationResponse> pendingInvitations) { this.pendingInvitations = pendingInvitations; }

  @Override
  public String toString() {
    return "MemberListResponse{members=" + (members != null ? members.size() : 0) +
        ", pendingInvitations=" + (pendingInvitations != null ? pendingInvitations.size() : 0) + "}";
  }
}
