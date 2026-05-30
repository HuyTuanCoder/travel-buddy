package travelbuddy.authservice.mapper;

import org.springframework.stereotype.Component;
import travelbuddy.authservice.dto.RegisterRequest;
import travelbuddy.authservice.model.Credential;

@Component
public class CredentialMapper {

  // Translates the React JSON (AuthRequest) into a Postgres row (Credential)
  public Credential toEntity(RegisterRequest request, String hashedPassword) {
    Credential credential = new Credential();
    credential.setEmail(request.getEmail());

    // We inject the hash here so the plain-text password NEVER touches the model
    credential.setPasswordHash(hashedPassword);

    return credential;
  }
}