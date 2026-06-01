package com.travelbuddy.itineraryservice.service;

import com.travelbuddy.itineraryservice.dto.*;
import com.travelbuddy.itineraryservice.exception.AccessDeniedException;
import com.travelbuddy.itineraryservice.exception.ItineraryNotFoundException;
import com.travelbuddy.itineraryservice.mapper.ItineraryMapper;
import com.travelbuddy.itineraryservice.model.*;
import com.travelbuddy.itineraryservice.repository.*;
import jakarta.transaction.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class ItineraryService {

  private static final Logger log = LoggerFactory.getLogger(ItineraryService.class);

  private final ItineraryRepository itineraryRepository;
  private final ItineraryMemberRepository memberRepository;
  private final ItineraryDayRepository dayRepository;
  private final TripStopRepository stopRepository;
  private final ItineraryMapper mapper;

  public ItineraryService(ItineraryRepository itineraryRepository,
                          ItineraryMemberRepository memberRepository,
                          ItineraryDayRepository dayRepository,
                          TripStopRepository stopRepository,
                          ItineraryMapper mapper) {
    this.itineraryRepository = itineraryRepository;
    this.memberRepository = memberRepository;
    this.dayRepository = dayRepository;
    this.stopRepository = stopRepository;
    this.mapper = mapper;
  }

  // ==================== POST /itineraries ====================

  @Transactional
  public ItineraryResponse createItinerary(CreateItineraryRequest request, String userId) {
    log.info("[createItinerary] >>> Input: {}, userId={}", request, userId);

    // 1. Map the request to a new itinerary entity and persist it
    Itinerary itinerary = mapper.toEntity(request, userId);
    Itinerary savedItinerary = itineraryRepository.save(itinerary);

    // 2. Auto-add the creator as an OWNER member with ACCEPTED status
    ItineraryMember ownerMember = new ItineraryMember();
    ownerMember.setItinerary(savedItinerary);
    ownerMember.setUserId(userId);
    ownerMember.setRole(MemberRole.OWNER);
    ownerMember.setStatus(MemberStatus.ACCEPTED);
    memberRepository.save(ownerMember);

    // 3. Map to response and return
    ItineraryResponse response = mapper.toItineraryResponse(savedItinerary);
    log.info("[createItinerary] <<< Output: {}", response);
    return response;
  }

  // ==================== GET /itineraries ====================

  public List<ItinerarySummaryResponse> listItineraries(String userId) {
    log.info("[listItineraries] >>> Input: userId={}", userId);

    // Fetch all trips the user has accepted, with itinerary data eagerly loaded via JOIN FETCH
    List<ItineraryMember> memberships = memberRepository.findByUserIdAndStatusWithItinerary(
        userId, MemberStatus.ACCEPTED);

    // Map each membership to a summary card (itinerary metadata + user's role)
    List<ItinerarySummaryResponse> responses = memberships.stream()
        .map(mapper::toSummaryResponse)
        .collect(Collectors.toList());

    log.info("[listItineraries] <<< Output: {} itineraries found", responses.size());
    return responses;
  }

  // ==================== GET /itineraries/{id} ====================

  public ItineraryDetailResponse getItineraryDetail(UUID itineraryId, String userId) {
    log.info("[getItineraryDetail] >>> Input: itineraryId={}, userId={}", itineraryId, userId);

    // 1. Verify the itinerary exists
    Itinerary itinerary = itineraryRepository.findById(itineraryId)
        .orElseThrow(() -> new ItineraryNotFoundException("Itinerary not found: " + itineraryId));

    // 2. Verify the user is a member of this trip (any role can view)
    verifyMembership(itineraryId, userId);

    // 3. Fetch all related data
    List<ItineraryMember> members = memberRepository.findByItineraryId(itineraryId);
    List<ItineraryDay> days = dayRepository.findByItineraryIdOrderByDayNumberAsc(itineraryId);

    // 4. Batch-fetch all stops for all days in one query, then group by day ID
    List<UUID> dayIds = days.stream().map(ItineraryDay::getId).collect(Collectors.toList());
    Map<UUID, List<TripStop>> stopsByDayId = dayIds.isEmpty()
        ? Map.of()
        : stopRepository.findByItineraryDayIdInOrderByVisitOrderAsc(dayIds).stream()
            .collect(Collectors.groupingBy(stop -> stop.getItineraryDay().getId()));

    // 5. Assemble the full nested response
    ItineraryDetailResponse response = mapper.toDetailResponse(itinerary, members, days, stopsByDayId);
    log.info("[getItineraryDetail] <<< Output: {}", response);
    return response;
  }

  // ==================== PUT /itineraries/{id} ====================

  @Transactional
  public ItineraryResponse updateItinerary(UUID itineraryId, UpdateItineraryRequest request, String userId) {
    log.info("[updateItinerary] >>> Input: itineraryId={}, {}, userId={}", itineraryId, request, userId);

    // 1. Verify the itinerary exists
    Itinerary itinerary = itineraryRepository.findById(itineraryId)
        .orElseThrow(() -> new ItineraryNotFoundException("Itinerary not found: " + itineraryId));

    // 2. Verify the user has OWNER or EDITOR role
    verifyEditPermission(itineraryId, userId);

    // 3. Apply only the non-null fields from the request (partial update)
    if (request.getTitle() != null) {
      itinerary.setTitle(request.getTitle());
    }
    if (request.getTimezone() != null) {
      itinerary.setTimezone(request.getTimezone());
    }
    if (request.getStatus() != null) {
      itinerary.setStatus(request.getStatus());
    }

    // 4. Save and return — @PreUpdate handles updatedAt timestamp
    Itinerary updatedItinerary = itineraryRepository.save(itinerary);
    ItineraryResponse response = mapper.toItineraryResponse(updatedItinerary);
    log.info("[updateItinerary] <<< Output: {}", response);
    return response;
  }

  // ==================== DELETE /itineraries/{id} ====================

  @Transactional
  public void deleteItinerary(UUID itineraryId, String userId) {
    log.info("[deleteItinerary] >>> Input: itineraryId={}, userId={}", itineraryId, userId);

    // 1. Verify the itinerary exists
    Itinerary itinerary = itineraryRepository.findById(itineraryId)
        .orElseThrow(() -> new ItineraryNotFoundException("Itinerary not found: " + itineraryId));

    // 2. Verify the user is the OWNER — only owners can delete a trip
    verifyOwnership(itineraryId, userId);

    // 3. Cascade delete in order: stops → days → members → itinerary
    List<ItineraryDay> days = dayRepository.findByItineraryIdOrderByDayNumberAsc(itineraryId);
    List<UUID> dayIds = days.stream().map(ItineraryDay::getId).collect(Collectors.toList());

    if (!dayIds.isEmpty()) {
      stopRepository.deleteByDayIds(dayIds);
    }
    dayRepository.deleteByItineraryId(itineraryId);
    memberRepository.deleteByItineraryId(itineraryId);
    itineraryRepository.delete(itinerary);

    log.info("[deleteItinerary] <<< Output: itinerary {} deleted successfully", itineraryId);
  }

  // ==================== RBAC Helpers ====================

  // Verifies the user belongs to this trip at all (any role)
  private ItineraryMember verifyMembership(UUID itineraryId, String userId) {
    return memberRepository.findByItineraryIdAndUserId(itineraryId, userId)
        .orElseThrow(() -> new AccessDeniedException(
            "User " + userId + " is not a member of itinerary " + itineraryId));
  }

  // Verifies the user is OWNER or EDITOR
  private void verifyEditPermission(UUID itineraryId, String userId) {
    ItineraryMember member = verifyMembership(itineraryId, userId);
    if (member.getRole() != MemberRole.OWNER && member.getRole() != MemberRole.EDITOR) {
      throw new AccessDeniedException("User " + userId + " does not have edit permission on itinerary " + itineraryId);
    }
  }

  // Verifies the user is the OWNER
  private void verifyOwnership(UUID itineraryId, String userId) {
    ItineraryMember member = verifyMembership(itineraryId, userId);
    if (member.getRole() != MemberRole.OWNER) {
      throw new AccessDeniedException("User " + userId + " is not the owner of itinerary " + itineraryId);
    }
  }
}
