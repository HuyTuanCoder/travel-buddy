package com.travelbuddy.itineraryservice.model;

import jakarta.persistence.*;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "itinerary_day", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"itinerary_id", "day_number"})
})
public class ItineraryDay {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "itinerary_id", nullable = false, updatable = false)
  private Itinerary itinerary;

  @Column(name = "day_number", nullable = false)
  private Integer dayNumber;

  @Column(name = "scheduled_date")
  private LocalDate scheduledDate;

  // --- Getters and Setters ---

  public UUID getId() {
    return id;
  }

  public void setId(UUID id) {
    this.id = id;
  }

  public Itinerary getItinerary() {
    return itinerary;
  }

  public void setItinerary(Itinerary itinerary) {
    this.itinerary = itinerary;
  }

  public Integer getDayNumber() {
    return dayNumber;
  }

  public void setDayNumber(Integer dayNumber) {
    this.dayNumber = dayNumber;
  }

  public LocalDate getScheduledDate() {
    return scheduledDate;
  }

  public void setScheduledDate(LocalDate scheduledDate) {
    this.scheduledDate = scheduledDate;
  }
}
