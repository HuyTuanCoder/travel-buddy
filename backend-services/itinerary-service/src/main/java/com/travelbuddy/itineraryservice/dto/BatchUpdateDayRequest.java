package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

public class BatchUpdateDayRequest {

    @NotNull
    private UUID dayId;

    @NotNull
    @Valid
    private List<BatchUpdateStopRequest> stops;

    public UUID getDayId() {
        return dayId;
    }

    public void setDayId(UUID dayId) {
        this.dayId = dayId;
    }

    public List<BatchUpdateStopRequest> getStops() {
        return stops;
    }

    public void setStops(List<BatchUpdateStopRequest> stops) {
        this.stops = stops;
    }
}
