package com.travelbuddy.itineraryservice.repository;

import com.travelbuddy.itineraryservice.model.TripStop;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface TripStopRepository extends JpaRepository<TripStop, UUID> {

  // Detail view: batch-fetch all stops across multiple days in one query (avoids N+1)
  List<TripStop> findByItineraryDayIdInOrderByVisitOrderAsc(List<UUID> itineraryDayIds);

  // Single day: fetch all stops for one day, sorted by visit order
  List<TripStop> findByItineraryDayIdOrderByVisitOrderAsc(UUID itineraryDayId);

  // Auto-order: find the highest visitOrder so we can append visitOrder = max + 1
  @Query("SELECT MAX(ts.visitOrder) FROM TripStop ts WHERE ts.itineraryDay.id = :dayId")
  Optional<Integer> findMaxVisitOrderByDayId(@Param("dayId") UUID dayId);

  // Cascade delete: remove all stops for a single day
  @Modifying
  @Query("DELETE FROM TripStop ts WHERE ts.itineraryDay.id = :dayId")
  void deleteByDayId(@Param("dayId") UUID dayId);

  // Cascade delete: remove all stops for a set of days being deleted
  @Modifying
  @Query("DELETE FROM TripStop ts WHERE ts.itineraryDay.id IN :dayIds")
  void deleteByDayIds(@Param("dayIds") List<UUID> dayIds);
}
