package com.travelbuddy.itineraryservice.repository;

import com.travelbuddy.itineraryservice.model.ItineraryDay;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ItineraryDayRepository extends JpaRepository<ItineraryDay, UUID> {

  // Detail view: list all days for a trip, sorted chronologically
  List<ItineraryDay> findByItineraryIdOrderByDayNumberAsc(UUID itineraryId);

  // Cascade delete: remove all days when an itinerary is deleted
  @Modifying
  @Query("DELETE FROM ItineraryDay d WHERE d.itinerary.id = :itineraryId")
  void deleteByItineraryId(@Param("itineraryId") UUID itineraryId);
}
