package com.travelbuddy.itineraryservice.model;

import jakarta.persistence.*;

import java.time.Instant;
import java.util.UUID;

/**
 * Ephemeral invitation record — exists only while PENDING.
 * Accept → delete this row + insert into itinerary_member.
 * Decline → delete this row.
 * The table self-cleans; no zombie rows.
 */
@Entity
@Table(name = "itinerary_invitation", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"itinerary_id", "user_id"})
})
public class ItineraryInvitation {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "itinerary_id", nullable = false, updatable = false)
  private Itinerary itinerary;

  @Column(name = "user_id", nullable = false, updatable = false)
  private String userId;

  // The role the user will receive when they accept
  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private MemberRole role;

  @Column(name = "invited_at", nullable = false, updatable = false)
  private Instant invitedAt;

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

  public Instant getInvitedAt() {
    return invitedAt;
  }

  public void setInvitedAt(Instant invitedAt) {
    this.invitedAt = invitedAt;
  }
}
