package com.travelbuddy.itineraryservice.repository;

import com.travelbuddy.itineraryservice.model.TripStop;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface TripStopRepository extends JpaRepository<TripStop, UUID> {

  // Detail view: batch-fetch all stops across multiple days in one query (avoids N+1)
  List<TripStop> findByItineraryDayIdInOrderByVisitOrderAsc(List<UUID> itineraryDayIds);

  // Cascade delete: remove all stops for a set of days being deleted
  @Modifying
  @Query("DELETE FROM TripStop ts WHERE ts.itineraryDay.id IN :dayIds")
  void deleteByDayIds(@Param("dayIds") List<UUID> dayIds);
}
