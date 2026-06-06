package com.travelbuddy.itineraryservice.exception;

public class AccessDeniedException extends RuntimeException {
  public AccessDeniedException(String message) {
    super(message);
  }
}
