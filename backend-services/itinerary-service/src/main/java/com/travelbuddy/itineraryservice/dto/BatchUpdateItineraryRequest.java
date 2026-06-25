package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import java.util.List;

public class BatchUpdateItineraryRequest {

    @NotNull
    @Valid
    private List<BatchUpdateDayRequest> days;

    public List<BatchUpdateDayRequest> getDays() {
        return days;
    }

    public void setDays(List<BatchUpdateDayRequest> days) {
        this.days = days;
    }
}
