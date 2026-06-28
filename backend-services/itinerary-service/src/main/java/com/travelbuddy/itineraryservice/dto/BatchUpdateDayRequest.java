package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;

public class BatchUpdateDayRequest {

    @NotBlank
    private String id;

    private Integer dayNumber;

    @NotNull
    @Valid
    private List<BatchUpdateStopRequest> stops;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public Integer getDayNumber() {
        return dayNumber;
    }

    public void setDayNumber(Integer dayNumber) {
        this.dayNumber = dayNumber;
    }

    public List<BatchUpdateStopRequest> getStops() {
        return stops;
    }

    public void setStops(List<BatchUpdateStopRequest> stops) {
        this.stops = stops;
    }
}
