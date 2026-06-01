package com.travelbuddy.itineraryservice.model;

import jakarta.persistence.*;

import java.math.BigDecimal;
import java.time.LocalTime;
import java.util.UUID;

@Entity
@Table(name = "trip_stop")
public class TripStop {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "itinerary_day_id", nullable = false, updatable = false)
  private ItineraryDay itineraryDay;

  @Column(name = "google_place_id", nullable = false)
  private String googlePlaceId;

  @Column(name = "visit_order", nullable = false)
  private Integer visitOrder;

  @Column(name = "arrival_time")
  private LocalTime arrivalTime;

  @Column(name = "departure_time")
  private LocalTime departureTime;

  @Enumerated(EnumType.STRING)
  @Column(name = "stop_type", nullable = false)
  private StopType stopType;

  @Column(name = "estimated_cost", precision = 10, scale = 2)
  private BigDecimal estimatedCost;

  @Column(name = "user_notes", columnDefinition = "TEXT")
  private String userNotes;

  // --- Getters and Setters ---

  public UUID getId() {
    return id;
  }

  public void setId(UUID id) {
    this.id = id;
  }

  public ItineraryDay getItineraryDay() {
    return itineraryDay;
  }

  public void setItineraryDay(ItineraryDay itineraryDay) {
    this.itineraryDay = itineraryDay;
  }

  public String getGooglePlaceId() {
    return googlePlaceId;
  }

  public void setGooglePlaceId(String googlePlaceId) {
    this.googlePlaceId = googlePlaceId;
  }

  public Integer getVisitOrder() {
    return visitOrder;
  }

  public void setVisitOrder(Integer visitOrder) {
    this.visitOrder = visitOrder;
  }

  public LocalTime getArrivalTime() {
    return arrivalTime;
  }

  public void setArrivalTime(LocalTime arrivalTime) {
    this.arrivalTime = arrivalTime;
  }

  public LocalTime getDepartureTime() {
    return departureTime;
  }

  public void setDepartureTime(LocalTime departureTime) {
    this.departureTime = departureTime;
  }

  public StopType getStopType() {
    return stopType;
  }

  public void setStopType(StopType stopType) {
    this.stopType = stopType;
  }

  public BigDecimal getEstimatedCost() {
    return estimatedCost;
  }

  public void setEstimatedCost(BigDecimal estimatedCost) {
    this.estimatedCost = estimatedCost;
  }

  public String getUserNotes() {
    return userNotes;
  }

  public void setUserNotes(String userNotes) {
    this.userNotes = userNotes;
  }
}
