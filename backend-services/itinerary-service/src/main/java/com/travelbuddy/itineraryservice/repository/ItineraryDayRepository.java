package com.travelbuddy.itineraryservice.repository;

import com.travelbuddy.itineraryservice.model.ItineraryDay;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ItineraryDayRepository extends JpaRepository<ItineraryDay, UUID> {

  // Detail view: list all days for a trip, sorted chronologically
  List<ItineraryDay> findByItineraryIdOrderByDayNumberAsc(UUID itineraryId);

  // Auto-number: find the highest dayNumber so we can append dayNumber = max + 1
  @Query("SELECT MAX(d.dayNumber) FROM ItineraryDay d WHERE d.itinerary.id = :itineraryId")
  Optional<Integer> findMaxDayNumberByItineraryId(@Param("itineraryId") UUID itineraryId);

  // Look up a specific day by trip and number (for AI tools)
  Optional<ItineraryDay> findByItineraryIdAndDayNumber(UUID itineraryId, Integer dayNumber);

  // Cascade delete: remove all days when an itinerary is deleted
  @Modifying
  @Query("DELETE FROM ItineraryDay d WHERE d.itinerary.id = :itineraryId")
  void deleteByItineraryId(@Param("itineraryId") UUID itineraryId);
}
