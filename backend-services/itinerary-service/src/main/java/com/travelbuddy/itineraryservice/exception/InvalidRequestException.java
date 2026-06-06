package com.travelbuddy.itineraryservice.exception;

public class InvalidRequestException extends RuntimeException {
  public InvalidRequestException(String message) {
    super(message);
  }
}
