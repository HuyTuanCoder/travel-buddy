package com.travelbuddy.locationservice.model;

import jakarta.persistence.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "place")
public class Place {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(name = "google_place_id", nullable = false, unique = true)
  private String googlePlaceId;

  @Column(name = "name", nullable = false)
  private String name;

  @Column(name = "formatted_address")
  private String formattedAddress;

  @Column(name = "latitude", nullable = false)
  private Double latitude;

  @Column(name = "longitude", nullable = false)
  private Double longitude;

  @Column(name = "photo_reference")
  private String photoReference;

  @Column(name = "place_types")
  private String placeTypes;

  @Column(name = "created_at", nullable = false, updatable = false)
  private Instant createdAt;

  @Column(name = "updated_at")
  private Instant updatedAt;

  @PrePersist
  protected void onCreate() {
    createdAt = Instant.now();
    updatedAt = Instant.now();
  }

  @PreUpdate
  protected void onUpdate() {
    updatedAt = Instant.now();
  }

  // --- Getters and Setters ---

  public UUID getId() { return id; }
  public void setId(UUID id) { this.id = id; }

  public String getGooglePlaceId() { return googlePlaceId; }
  public void setGooglePlaceId(String googlePlaceId) { this.googlePlaceId = googlePlaceId; }

  public String getName() { return name; }
  public void setName(String name) { this.name = name; }

  public String getFormattedAddress() { return formattedAddress; }
  public void setFormattedAddress(String formattedAddress) { this.formattedAddress = formattedAddress; }

  public Double getLatitude() { return latitude; }
  public void setLatitude(Double latitude) { this.latitude = latitude; }

  public Double getLongitude() { return longitude; }
  public void setLongitude(Double longitude) { this.longitude = longitude; }

  public String getPhotoReference() { return photoReference; }
  public void setPhotoReference(String photoReference) { this.photoReference = photoReference; }

  public String getPlaceTypes() { return placeTypes; }
  public void setPlaceTypes(String placeTypes) { this.placeTypes = placeTypes; }

  public Instant getCreatedAt() { return createdAt; }
  public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

  public Instant getUpdatedAt() { return updatedAt; }
  public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
}
