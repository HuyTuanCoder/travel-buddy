package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public class SwapDaysRequest {

    @NotNull
    private Integer dayA;

    @NotNull
    private Integer dayB;

    public SwapDaysRequest() {}

    public SwapDaysRequest(Integer dayA, Integer dayB) {
        this.dayA = dayA;
        this.dayB = dayB;
    }

    public Integer getDayA() { return dayA; }
    public void setDayA(Integer dayA) { this.dayA = dayA; }

    public Integer getDayB() { return dayB; }
    public void setDayB(Integer dayB) { this.dayB = dayB; }
}
