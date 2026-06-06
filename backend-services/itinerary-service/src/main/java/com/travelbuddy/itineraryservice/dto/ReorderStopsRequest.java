package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.constraints.NotEmpty;

import java.util.List;
import java.util.UUID;

/**
 * Request to reorder stops within a day via drag-and-drop.
 * The client sends the full ordered list of stop IDs — the service assigns visitOrder
 * based on list index (1-based).
 */
public class ReorderStopsRequest {

  @NotEmpty(message = "Stop IDs list cannot be empty")
  private List<UUID> stopIds;

  public ReorderStopsRequest() {}

  public ReorderStopsRequest(List<UUID> stopIds) {
    this.stopIds = stopIds;
  }

  public List<UUID> getStopIds() { return stopIds; }
  public void setStopIds(List<UUID> stopIds) { this.stopIds = stopIds; }

  @Override
  public String toString() {
    return "ReorderStopsRequest{stopIds=" + (stopIds != null ? stopIds.size() + " items" : "null") + "}";
  }
}
