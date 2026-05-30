package travelbuddy.authservice.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {
  @ExceptionHandler(BadCredentialsException.class)
  public ResponseEntity<Map<String, String>> handleBadCredentials(BadCredentialsException ex) {
    Map<String, String> errorResponse = new HashMap<>();

    errorResponse.put("error", "Unauthorized");
    errorResponse.put("message", "Invalid email or password");

    // 401 Unauthorized is the exact HTTP standard for failed logins
    return new ResponseEntity<>(errorResponse, HttpStatus.UNAUTHORIZED);
  }

  @ExceptionHandler(EmailAlreadyExistsException.class)
  public ResponseEntity<Map<String, String>> handleEmailExists(EmailAlreadyExistsException ex) {
    Map<String, String> errorResponse = new HashMap<>();

    errorResponse.put("error", "Conflict");
    errorResponse.put("message", ex.getMessage());

    // 409 Conflict is the exact HTTP standard for "this resource already exists"
    return new ResponseEntity<>(errorResponse, HttpStatus.CONFLICT);
  }
}
