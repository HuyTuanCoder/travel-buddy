package travelbuddy.authservice.service;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import travelbuddy.authservice.dto.AuthResponse;
import travelbuddy.authservice.dto.LoginRequest;
import travelbuddy.authservice.dto.RegisterRequest;
import travelbuddy.authservice.exception.EmailAlreadyExistsException;
import travelbuddy.authservice.mapper.CredentialMapper;
import travelbuddy.authservice.model.Credential;
import travelbuddy.authservice.repository.CredentialRepository;
import travelbuddy.authservice.util.JwtService;

@Service
public class AuthService {

  private final CredentialRepository repository;
  private final PasswordEncoder passwordEncoder;
  private final CredentialMapper mapper;
  private final AuthenticationManager authenticationManager;
  private final JwtService jwtService;

  public AuthService(CredentialRepository repository, PasswordEncoder passwordEncoder,
                     CredentialMapper mapper, AuthenticationManager authenticationManager,
                     JwtService jwtService) {
    this.repository = repository;
    this.passwordEncoder = passwordEncoder;
    this.mapper = mapper;
    this.authenticationManager = authenticationManager;
    this.jwtService = jwtService;
  }

  public AuthResponse register(RegisterRequest request) {
    // 1. Check if the user already exists
    if (repository.findByEmail(request.getEmail()).isPresent()) {
      throw new EmailAlreadyExistsException("Email is already registered!");
    }

    // 2. Hash the raw password
    String hashedPassword = passwordEncoder.encode(request.getPassword());

    // 3. Map and save to Postgres
    Credential credential = mapper.toEntity(request, hashedPassword);
    Credential savedCredential = repository.save(credential);

    // 4. Generate and return the JWT
    String token = jwtService.generateToken(savedCredential);
    return new AuthResponse(token);
  }

  public AuthResponse login(LoginRequest request) {
    // 1. Let Spring Security do the heavy lifting (this automatically checks the hash)
    authenticationManager.authenticate(
        new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword())
    );

    // 2. If the code reaches this line, the password was correct. Fetch the user.
    Credential credential = repository.findByEmail(request.getEmail())
        .orElseThrow(() -> new BadCredentialsException("Invalid email or password"));

    // 3. Generate and return the JWT
    String token = jwtService.generateToken(credential);
    return new AuthResponse(token);
  }
}