package com.travelbuddy.itineraryservice.dto;

import com.travelbuddy.itineraryservice.model.ItineraryStatus;
import jakarta.validation.constraints.Size;

public class UpdateItineraryRequest {

  // All fields optional — only non-null values get applied
  @Size(min = 1, max = 255, message = "Title must be between 1 and 255 characters")
  private String title;

  private String timezone;

  private ItineraryStatus status;

  public UpdateItineraryRequest() {}

  public String getTitle() { return title; }
  public void setTitle(String title) { this.title = title; }

  public String getTimezone() { return timezone; }
  public void setTimezone(String timezone) { this.timezone = timezone; }

  public ItineraryStatus getStatus() { return status; }
  public void setStatus(ItineraryStatus status) { this.status = status; }

  @Override
  public String toString() {
    return "UpdateItineraryRequest{title='" + title + "', timezone='" + timezone + "', status=" + status + "}";
  }
}
