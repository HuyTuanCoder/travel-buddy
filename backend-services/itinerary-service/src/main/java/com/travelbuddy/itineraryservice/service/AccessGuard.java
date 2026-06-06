package com.travelbuddy.itineraryservice.service;

import com.travelbuddy.itineraryservice.exception.AccessDeniedException;
import com.travelbuddy.itineraryservice.exception.ItineraryNotFoundException;
import com.travelbuddy.itineraryservice.model.Itinerary;
import com.travelbuddy.itineraryservice.model.ItineraryMember;
import com.travelbuddy.itineraryservice.model.MemberRole;
import com.travelbuddy.itineraryservice.repository.ItineraryMemberRepository;
import com.travelbuddy.itineraryservice.repository.ItineraryRepository;
import org.springframework.stereotype.Component;

import java.util.UUID;

/**
 * Shared precondition checks used across ItineraryService, MemberService, and TimelineService.
 * Handles two concerns:
 *   1. Resource validation — does the itinerary exist?
 *   2. Permission enforcement — is the user a member / editor / owner?
 */
@Component
public class AccessGuard {

  private final ItineraryRepository itineraryRepository;
  private final ItineraryMemberRepository memberRepository;

  public AccessGuard(ItineraryRepository itineraryRepository,
                     ItineraryMemberRepository memberRepository) {
    this.itineraryRepository = itineraryRepository;
    this.memberRepository = memberRepository;
  }

  // --- Resource Validation ---

  // Returns the itinerary or throws 404
  public Itinerary findItinerary(UUID itineraryId) {
    return itineraryRepository.findById(itineraryId)
        .orElseThrow(() -> new ItineraryNotFoundException("Itinerary not found: " + itineraryId));
  }

  // Checks existence without loading the full entity
  public void verifyItineraryExists(UUID itineraryId) {
    if (!itineraryRepository.existsById(itineraryId)) {
      throw new ItineraryNotFoundException("Itinerary not found: " + itineraryId);
    }
  }

  // --- Permission Enforcement ---

  // Any role — verifies the user belongs to this trip at all
  public ItineraryMember verifyMembership(UUID itineraryId, String userId) {
    return memberRepository.findByItineraryIdAndUserId(itineraryId, userId)
        .orElseThrow(() -> new AccessDeniedException(
            "User " + userId + " is not a member of itinerary " + itineraryId));
  }

  // OWNER or EDITOR — for modifying days, stops, and trip settings
  public void verifyEditPermission(UUID itineraryId, String userId) {
    ItineraryMember member = verifyMembership(itineraryId, userId);
    if (member.getRole() != MemberRole.OWNER && member.getRole() != MemberRole.EDITOR) {
      throw new AccessDeniedException(
          "User " + userId + " does not have edit permission on itinerary " + itineraryId);
    }
  }

  // OWNER only — for deleting trips, inviting members, kicking members
  public void verifyOwnership(UUID itineraryId, String userId) {
    ItineraryMember member = verifyMembership(itineraryId, userId);
    if (member.getRole() != MemberRole.OWNER) {
      throw new AccessDeniedException(
          "User " + userId + " is not the owner of itinerary " + itineraryId);
    }
  }
}
