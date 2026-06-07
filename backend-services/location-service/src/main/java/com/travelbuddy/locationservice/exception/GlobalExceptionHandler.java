package com.travelbuddy.locationservice.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

  private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

  // Catches @Valid failures (e.g., @NotBlank)
  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<Map<String, Object>> handleValidationErrors(MethodArgumentNotValidException ex) {
    Map<String, String> fieldErrors = new HashMap<>();
    ex.getBindingResult().getFieldErrors().forEach(error ->
        fieldErrors.put(error.getField(), error.getDefaultMessage())
    );

    Map<String, Object> errorResponse = new HashMap<>();
    errorResponse.put("error", "Validation Failed");
    errorResponse.put("message", "One or more fields are invalid");
    errorResponse.put("details", fieldErrors);

    log.warn("[Validation Error] {}", fieldErrors);
    return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
  }

  // 404 — location not found
  @ExceptionHandler(LocationNotFoundException.class)
  public ResponseEntity<Map<String, String>> handleNotFound(LocationNotFoundException ex) {
    Map<String, String> errorResponse = new HashMap<>();
    errorResponse.put("error", "Not Found");
    errorResponse.put("message", ex.getMessage());

    log.warn("[Not Found] {}", ex.getMessage());
    return new ResponseEntity<>(errorResponse, HttpStatus.NOT_FOUND);
  }

  // 502 — Bad Gateway (Google Places API failure)
  @ExceptionHandler(GooglePlacesApiException.class)
  public ResponseEntity<Map<String, String>> handleGooglePlacesApi(GooglePlacesApiException ex) {
    Map<String, String> errorResponse = new HashMap<>();
    errorResponse.put("error", "Bad Gateway");
    errorResponse.put("message", ex.getMessage());

    log.error("[Bad Gateway] {}", ex.getMessage());
    return new ResponseEntity<>(errorResponse, HttpStatus.BAD_GATEWAY);
  }

  // Catch-all for any unhandled exceptions
  @ExceptionHandler(Exception.class)
  public ResponseEntity<Map<String, String>> handleGeneric(Exception ex) {
    Map<String, String> errorResponse = new HashMap<>();
    errorResponse.put("error", "Internal Server Error");
    errorResponse.put("message", "An unexpected error occurred");

    log.error("[Unhandled Exception] {}", ex.getMessage(), ex);
    return new ResponseEntity<>(errorResponse, HttpStatus.INTERNAL_SERVER_ERROR);
  }
}
