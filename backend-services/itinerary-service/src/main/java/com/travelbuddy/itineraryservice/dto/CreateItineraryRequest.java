package com.travelbuddy.itineraryservice.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class CreateItineraryRequest {

  @NotBlank(message = "Title is required")
  @Size(max = 255, message = "Title must be 255 characters or less")
  private String title;

  @NotBlank(message = "Timezone is required")
  private String timezone;

  public CreateItineraryRequest() {
  }

  public CreateItineraryRequest(String title, String timezone) {
    this.title = title;
    this.timezone = timezone;
  }

  public String getTitle() {
    return title;
  }

  public void setTitle(String title) {
    this.title = title;
  }

  public String getTimezone() {
    return timezone;
  }

  public void setTimezone(String timezone) {
    this.timezone = timezone;
  }

  @Override
  public String toString() {
    return "CreateItineraryRequest{title='" + title + "', timezone='" + timezone + "'}";
  }
}
