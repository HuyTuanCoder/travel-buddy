package com.travelbuddy.itineraryservice.service;

import com.travelbuddy.itineraryservice.dto.*;
import com.travelbuddy.itineraryservice.exception.AccessDeniedException;
import com.travelbuddy.itineraryservice.exception.ConflictException;
import com.travelbuddy.itineraryservice.exception.InvalidRequestException;
import com.travelbuddy.itineraryservice.exception.ItineraryNotFoundException;
import com.travelbuddy.itineraryservice.mapper.ItineraryMapper;
import com.travelbuddy.itineraryservice.model.*;
import com.travelbuddy.itineraryservice.repository.ItineraryInvitationRepository;
import com.travelbuddy.itineraryservice.repository.ItineraryMemberRepository;
import com.travelbuddy.itineraryservice.repository.ItineraryRepository;
import jakarta.transaction.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class MemberService {

  private static final Logger log = LoggerFactory.getLogger(MemberService.class);

  private final ItineraryRepository itineraryRepository;
  private final ItineraryMemberRepository memberRepository;
  private final ItineraryInvitationRepository invitationRepository;
  private final ItineraryMapper mapper;
  private final AccessGuard accessGuard;

  public MemberService(ItineraryRepository itineraryRepository,
                       ItineraryMemberRepository memberRepository,
                       ItineraryInvitationRepository invitationRepository,
                       ItineraryMapper mapper,
                       AccessGuard accessGuard) {
    this.itineraryRepository = itineraryRepository;
    this.memberRepository = memberRepository;
    this.invitationRepository = invitationRepository;
    this.mapper = mapper;
    this.accessGuard = accessGuard;
  }

  // ==================== GET /itineraries/{id}/members ====================

  public MemberListResponse getMembers(UUID itineraryId, String userId) {
    log.info("[getMembers] >>> Input: itineraryId={}, userId={}", itineraryId, userId);

    accessGuard.verifyItineraryExists(itineraryId);
    accessGuard.verifyMembership(itineraryId, userId); // Any member can view the list

    List<ItineraryMember> confirmedMembers = memberRepository.findByItineraryId(itineraryId);
    List<ItineraryInvitation> pendingInvitations = invitationRepository.findByItineraryId(itineraryId);

    List<ItineraryMemberResponse> memberResponses = confirmedMembers.stream()
        .map(mapper::toMemberResponse)
        .collect(Collectors.toList());

    List<InvitationResponse> inviteResponses = pendingInvitations.stream()
        .map(mapper::toInvitationResponse)
        .collect(Collectors.toList());

    MemberListResponse response = new MemberListResponse(memberResponses, inviteResponses);
    log.info("[getMembers] <<< Output: {} members, {} invites", memberResponses.size(), inviteResponses.size());
    return response;
  }

  // ==================== POST /itineraries/{id}/invitations ====================

  @Transactional
  public InvitationResponse inviteMember(UUID itineraryId, InviteRequest request, String userId) {
    log.info("[inviteMember] >>> Input: itineraryId={}, request={}, userId={}", itineraryId, request, userId);

    accessGuard.verifyItineraryExists(itineraryId);
    accessGuard.verifyOwnership(itineraryId, userId); // Only OWNER can invite

    if (request.getInviteeUserId().equals(userId)) {
      throw new InvalidRequestException("You cannot invite yourself");
    }
    if (request.getRole() == MemberRole.OWNER) {
      throw new InvalidRequestException("Cannot invite a user as OWNER");
    }

    // Check if already a member
    if (memberRepository.findByItineraryIdAndUserId(itineraryId, request.getInviteeUserId()).isPresent()) {
      throw new ConflictException("User is already a member of this itinerary");
    }

    // Check if already invited
    if (invitationRepository.findByItineraryIdAndUserId(itineraryId, request.getInviteeUserId()).isPresent()) {
      throw new ConflictException("User is already invited to this itinerary");
    }

    Itinerary itinerary = itineraryRepository.findById(itineraryId).get();

    ItineraryInvitation invitation = new ItineraryInvitation();
    invitation.setItinerary(itinerary);
    invitation.setUserId(request.getInviteeUserId());
    invitation.setRole(request.getRole());

    ItineraryInvitation savedInvitation = invitationRepository.save(invitation);
    InvitationResponse response = mapper.toInvitationResponse(savedInvitation);

    log.info("[inviteMember] <<< Output: {}", response);
    return response;
  }

  // ==================== PUT /itineraries/invitations/{id}/respond ====================

  @Transactional
  public Object respondToInvitation(UUID invitationId, InvitationActionRequest request, String userId) {
    log.info("[respondToInvitation] >>> Input: invitationId={}, request={}, userId={}", invitationId, request, userId);

    ItineraryInvitation invitation = invitationRepository.findById(invitationId)
        .orElseThrow(() -> new ItineraryNotFoundException("Invitation not found: " + invitationId));

    if (!invitation.getUserId().equals(userId)) {
      throw new AccessDeniedException("You can only respond to your own invitations");
    }

    if ("ACCEPTED".equalsIgnoreCase(request.getAction())) {
      // 1. Create member
      ItineraryMember newMember = new ItineraryMember();
      newMember.setItinerary(invitation.getItinerary());
      newMember.setUserId(invitation.getUserId());
      newMember.setRole(invitation.getRole());
      memberRepository.save(newMember);

      // 2. Delete invitation
      invitationRepository.delete(invitation);

      ItineraryMemberResponse response = mapper.toMemberResponse(newMember);
      log.info("[respondToInvitation] <<< Output (Accepted): {}", response);
      return response;

    } else if ("DECLINED".equalsIgnoreCase(request.getAction())) {
      // 1. Delete invitation
      invitationRepository.delete(invitation);
      log.info("[respondToInvitation] <<< Output (Declined)");
      return java.util.Map.of("message", "Invitation declined");

    } else {
      throw new InvalidRequestException("Action must be ACCEPTED or DECLINED");
    }
  }

  // ==================== DELETE /itineraries/{id}/members/{targetUserId} ====================

  @Transactional
  public void removeMemberOrRevokeInvite(UUID itineraryId, String targetUserId, String userId) {
    log.info("[removeMemberOrRevokeInvite] >>> Input: itineraryId={}, targetUserId={}, userId={}", itineraryId, targetUserId, userId);

    accessGuard.verifyItineraryExists(itineraryId);

    boolean isSelfRemoval = targetUserId.equals(userId);

    // If leaving, verify they are a member. If kicking, verify they are OWNER.
    if (isSelfRemoval) {
       accessGuard.verifyMembership(itineraryId, userId);
       
       // Owner cannot leave, they must delete the trip
       ItineraryMember selfMember = memberRepository.findByItineraryIdAndUserId(itineraryId, userId).get();
       if (selfMember.getRole() == MemberRole.OWNER) {
           throw new InvalidRequestException("Owner cannot leave the itinerary. Delete it or transfer ownership instead.");
       }
    } else {
       accessGuard.verifyOwnership(itineraryId, userId);
    }

    // Try to find in member table
    Optional<ItineraryMember> memberOpt = memberRepository.findByItineraryIdAndUserId(itineraryId, targetUserId);
    if (memberOpt.isPresent()) {
        if (!isSelfRemoval && memberOpt.get().getRole() == MemberRole.OWNER) {
             throw new InvalidRequestException("Cannot kick the owner");
        }
        memberRepository.delete(memberOpt.get());
        log.info("[removeMemberOrRevokeInvite] <<< Output: Removed from members");
        return;
    }

    // If not a member, owner might be trying to revoke a pending invite
    if (!isSelfRemoval) {
        Optional<ItineraryInvitation> inviteOpt = invitationRepository.findByItineraryIdAndUserId(itineraryId, targetUserId);
        if (inviteOpt.isPresent()) {
            invitationRepository.delete(inviteOpt.get());
            log.info("[removeMemberOrRevokeInvite] <<< Output: Revoked pending invite");
            return;
        }
    }

    throw new ItineraryNotFoundException("Target user is not a member or invited to this itinerary");
  }

  // ==================== PUT /itineraries/{id}/members/{targetUserId}/role ====================

  @Transactional
  public ItineraryMemberResponse updateMemberRole(UUID itineraryId, String targetUserId, UpdateMemberRoleRequest request, String userId) {
    log.info("[updateMemberRole] >>> Input: itineraryId={}, targetUserId={}, role={}, userId={}", itineraryId, targetUserId, request.getRole(), userId);

    accessGuard.verifyItineraryExists(itineraryId);
    accessGuard.verifyOwnership(itineraryId, userId);

    if (targetUserId.equals(userId)) {
      throw new InvalidRequestException("You cannot change your own role");
    }

    if (request.getRole() == MemberRole.OWNER) {
      throw new InvalidRequestException("Cannot change role to OWNER using this endpoint. Use the transfer-ownership endpoint instead.");
    }

    ItineraryMember member = memberRepository.findByItineraryIdAndUserId(itineraryId, targetUserId)
        .orElseThrow(() -> new ItineraryNotFoundException("Target user is not a member of this itinerary"));

    member.setRole(request.getRole());
    ItineraryMember updatedMember = memberRepository.save(member);

    ItineraryMemberResponse response = mapper.toMemberResponse(updatedMember);
    log.info("[updateMemberRole] <<< Output: {}", response);
    return response;
  }

  // ==================== PUT /itineraries/{id}/members/{targetUserId}/transfer-ownership ====================

  @Transactional
  public ItineraryMemberResponse transferOwnership(UUID itineraryId, String targetUserId, String userId) {
    log.info("[transferOwnership] >>> Input: itineraryId={}, targetUserId={}, userId={}", itineraryId, targetUserId, userId);

    accessGuard.verifyItineraryExists(itineraryId);
    accessGuard.verifyOwnership(itineraryId, userId);

    if (targetUserId.equals(userId)) {
      throw new InvalidRequestException("You already own this itinerary");
    }

    ItineraryMember currentOwner = memberRepository.findByItineraryIdAndUserId(itineraryId, userId)
        .orElseThrow(() -> new AccessDeniedException("You are not a member of this itinerary"));

    ItineraryMember newOwner = memberRepository.findByItineraryIdAndUserId(itineraryId, targetUserId)
        .orElseThrow(() -> new ItineraryNotFoundException("Target user is not a member of this itinerary"));

    // Demote current owner to EDITOR
    currentOwner.setRole(MemberRole.EDITOR);
    memberRepository.save(currentOwner);

    // Promote new owner
    newOwner.setRole(MemberRole.OWNER);
    ItineraryMember updatedNewOwner = memberRepository.save(newOwner);

    ItineraryMemberResponse response = mapper.toMemberResponse(updatedNewOwner);
    log.info("[transferOwnership] <<< Output: {}", response);
    return response;
  }

}
