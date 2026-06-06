package com.travelbuddy.itineraryservice.exception;

public class ItineraryNotFoundException extends RuntimeException {
  public ItineraryNotFoundException(String message) {
    super(message);
  }
}
