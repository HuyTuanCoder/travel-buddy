package com.travelbuddy.itineraryservice.repository;

import com.travelbuddy.itineraryservice.model.ItineraryInvitation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ItineraryInvitationRepository extends JpaRepository<ItineraryInvitation, UUID> {

  // Check if an invitation already exists for this user on this trip
  Optional<ItineraryInvitation> findByItineraryIdAndUserId(UUID itineraryId, String userId);

  // List all pending invitations for a specific trip (for the members panel)
  List<ItineraryInvitation> findByItineraryId(UUID itineraryId);

  // List all pending invitations for a user (for a "You've been invited" inbox)
  List<ItineraryInvitation> findByUserId(String userId);

  // Cascade delete: remove all invitations when an itinerary is deleted
  @Modifying
  @Query("DELETE FROM ItineraryInvitation inv WHERE inv.itinerary.id = :itineraryId")
  void deleteByItineraryId(@Param("itineraryId") UUID itineraryId);
}
