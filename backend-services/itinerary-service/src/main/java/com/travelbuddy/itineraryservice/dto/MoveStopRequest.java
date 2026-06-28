package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.UUID;

@Data
public class MoveStopRequest {

    @NotNull(message = "targetDayId is required")
    private UUID targetDayId;

    private Integer targetVisitOrder; // Optional: If null, append to end of day. If provided, insert at index.
}
