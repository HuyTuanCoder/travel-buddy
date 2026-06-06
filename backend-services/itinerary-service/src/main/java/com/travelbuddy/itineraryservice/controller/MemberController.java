package com.travelbuddy.itineraryservice.controller;

import com.travelbuddy.itineraryservice.dto.InvitationActionRequest;
import com.travelbuddy.itineraryservice.dto.InviteRequest;
import com.travelbuddy.itineraryservice.dto.MemberListResponse;
import com.travelbuddy.itineraryservice.service.MemberService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/itineraries")
public class MemberController {

  private static final Logger log = LoggerFactory.getLogger(MemberController.class);

  private final MemberService memberService;

  public MemberController(MemberService memberService) {
    this.memberService = memberService;
  }

  // GET /itineraries/{id}/members — list confirmed members and pending invites
  @GetMapping("/{id}/members")
  public ResponseEntity<MemberListResponse> getMembers(
      @PathVariable UUID id,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] GET /itineraries/{}/members | userId={}", id, userId);
    MemberListResponse response = memberService.getMembers(id, userId);
    return ResponseEntity.ok(response);
  }

  // POST /itineraries/{id}/invitations — invite a user to the trip
  @PostMapping("/{id}/invitations")
  public ResponseEntity<?> inviteMember(
      @PathVariable UUID id,
      @Valid @RequestBody InviteRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] POST /itineraries/{}/invitations | userId={}", id, userId);
    Object response = memberService.inviteMember(id, request, userId);
    return new ResponseEntity<>(response, HttpStatus.CREATED);
  }

  // PUT /itineraries/invitations/{invitationId}/respond — accept or decline
  @PutMapping("/invitations/{invitationId}/respond")
  public ResponseEntity<?> respondToInvitation(
      @PathVariable UUID invitationId,
      @Valid @RequestBody InvitationActionRequest request,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] PUT /itineraries/invitations/{}/respond | userId={}", invitationId, userId);
    Object response = memberService.respondToInvitation(invitationId, request, userId);
    return ResponseEntity.ok(response);
  }

  // DELETE /itineraries/{id}/members/{targetUserId} — kick a member or leave voluntarily
  @DeleteMapping("/{id}/members/{targetUserId}")
  public ResponseEntity<Void> removeMember(
      @PathVariable UUID id,
      @PathVariable String targetUserId,
      @RequestHeader("X-User-Id") String userId) {

    log.info("[Controller] DELETE /itineraries/{}/members/{} | userId={}", id, targetUserId, userId);
    memberService.removeMemberOrRevokeInvite(id, targetUserId, userId);
    return ResponseEntity.noContent().build();
  }
}
