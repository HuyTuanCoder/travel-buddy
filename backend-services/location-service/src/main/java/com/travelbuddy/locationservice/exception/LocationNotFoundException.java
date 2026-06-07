package com.travelbuddy.locationservice.exception;

public class LocationNotFoundException extends RuntimeException {
  public LocationNotFoundException(String message) {
    super(message);
  }
}
