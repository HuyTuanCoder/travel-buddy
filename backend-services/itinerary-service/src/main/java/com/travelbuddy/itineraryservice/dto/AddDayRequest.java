package com.travelbuddy.itineraryservice.dto;

import java.time.LocalDate;

/**
 * Request to append a new day to a trip timeline.
 * dayNumber is auto-calculated by the service (max + 1), scheduledDate is optional.
 */
public class AddDayRequest {

  private LocalDate scheduledDate;

  public AddDayRequest() {}

  public AddDayRequest(LocalDate scheduledDate) {
    this.scheduledDate = scheduledDate;
  }

  public LocalDate getScheduledDate() { return scheduledDate; }
  public void setScheduledDate(LocalDate scheduledDate) { this.scheduledDate = scheduledDate; }

  @Override
  public String toString() {
    return "AddDayRequest{scheduledDate=" + scheduledDate + "}";
  }
}
