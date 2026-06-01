package com.travelbuddy.itineraryservice.model;

import jakarta.persistence.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "itinerary_member", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"itinerary_id", "user_id"})
})
public class ItineraryMember {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "itinerary_id", nullable = false, updatable = false)
  private Itinerary itinerary;

  @Column(name = "user_id", nullable = false, updatable = false)
  private String userId;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private MemberRole role;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private MemberStatus status = MemberStatus.PENDING;

  @Column(name = "invited_at", nullable = false, updatable = false)
  private Instant invitedAt;

  @Column(name = "joined_at")
  private Instant joinedAt;

  @PrePersist
  protected void onCreate() {
    invitedAt = Instant.now();
  }

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

  public String getUserId() {
    return userId;
  }

  public void setUserId(String userId) {
    this.userId = userId;
  }

  public MemberRole getRole() {
    return role;
  }

  public void setRole(MemberRole role) {
    this.role = role;
  }

  public MemberStatus getStatus() {
    return status;
  }

  public void setStatus(MemberStatus status) {
    this.status = status;
  }

  public Instant getInvitedAt() {
    return invitedAt;
  }

  public void setInvitedAt(Instant invitedAt) {
    this.invitedAt = invitedAt;
  }

  public Instant getJoinedAt() {
    return joinedAt;
  }

  public void setJoinedAt(Instant joinedAt) {
    this.joinedAt = joinedAt;
  }
}
