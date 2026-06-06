package com.travelbuddy.itineraryservice.repository;

import com.travelbuddy.itineraryservice.model.ItineraryMember;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ItineraryMemberRepository extends JpaRepository<ItineraryMember, UUID> {

  // RBAC check: if a row exists, the user is a confirmed member. No status filtering needed.
  Optional<ItineraryMember> findByItineraryIdAndUserId(UUID itineraryId, String userId);

  // List view: fetch all trips the user belongs to, JOIN FETCH to avoid N+1 on itinerary data
  @Query("SELECT im FROM ItineraryMember im JOIN FETCH im.itinerary WHERE im.userId = :userId")
  List<ItineraryMember> findByUserIdWithItinerary(@Param("userId") String userId);

  // Detail view: list all confirmed participants of a specific trip
  List<ItineraryMember> findByItineraryId(UUID itineraryId);

  // Cascade delete: remove all members when an itinerary is deleted
  @Modifying
  @Query("DELETE FROM ItineraryMember im WHERE im.itinerary.id = :itineraryId")
  void deleteByItineraryId(@Param("itineraryId") UUID itineraryId);
}
