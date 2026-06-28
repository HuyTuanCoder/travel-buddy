package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public class MoveStopRequest {

    @NotNull(message = "targetDayId is required")
    private UUID targetDayId;

    private Integer targetVisitOrder; // Optional: If null, append to end of day. If provided, insert at index.

    public UUID getTargetDayId() {
        return targetDayId;
    }

    public void setTargetDayId(UUID targetDayId) {
        this.targetDayId = targetDayId;
    }

    public Integer getTargetVisitOrder() {
        return targetVisitOrder;
    }

    public void setTargetVisitOrder(Integer targetVisitOrder) {
        this.targetVisitOrder = targetVisitOrder;
    }
}
