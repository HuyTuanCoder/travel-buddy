package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.StopType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalTime;

public class BatchUpdateStopRequest {

    // Could be a real UUID or a temporary string like "temp-123"
    @NotBlank
    private String id;

    // This is the location string mapping from the AI payload
    @NotBlank
    private String googlePlaceId;

    private String locationName;
    private String address;

    @NotNull
    private StopType stopType;

    private String userNotes;
    private LocalTime arrivalTime;
    private LocalTime departureTime;
    private BigDecimal estimatedCost;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getGooglePlaceId() {
        return googlePlaceId;
    }

    public void setGooglePlaceId(String googlePlaceId) {
        this.googlePlaceId = googlePlaceId;
    }

    public String getLocationName() {
        return locationName;
    }

    public void setLocationName(String locationName) {
        this.locationName = locationName;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public StopType getStopType() {
        return stopType;
    }

    public void setStopType(StopType stopType) {
        this.stopType = stopType;
    }

    public String getUserNotes() {
        return userNotes;
    }

    public void setUserNotes(String userNotes) {
        this.userNotes = userNotes;
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

    public BigDecimal getEstimatedCost() {
        return estimatedCost;
    }

    public void setEstimatedCost(BigDecimal estimatedCost) {
        this.estimatedCost = estimatedCost;
    }
}
