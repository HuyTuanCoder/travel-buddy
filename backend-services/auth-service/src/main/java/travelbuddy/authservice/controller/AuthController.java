package travelbuddy.authservice.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import travelbuddy.authservice.dto.AuthResponse;
import travelbuddy.authservice.dto.LoginRequest;
import travelbuddy.authservice.dto.RegisterRequest;
import travelbuddy.authservice.service.AuthService;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

  private final AuthService authService;

  public AuthController(AuthService authService) {
    this.authService = authService;
  }

  @PostMapping("/register")
  public ResponseEntity<AuthResponse> register(@RequestBody RegisterRequest request) {
    // We return a 201 Created status for new resources
    return new ResponseEntity<>(authService.register(request), HttpStatus.CREATED);
  }

  @PostMapping("/login")
  public ResponseEntity<AuthResponse> login(@RequestBody LoginRequest request) {
    // We return a standard 200 OK for successful logins
    return ResponseEntity.ok(authService.login(request));
  }
}