package travelbuddy.authservice.util;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import travelbuddy.authservice.model.Credential;
import java.security.Key;
import java.util.Date;

@Service
public class JwtService {
  @Value("${jwt.secret}")
  private String secretKey;

  public String generateToken(Credential credential) {
    return Jwts.builder()
        // Embed the UUID as the main subject of the token
        .setSubject(credential.getId().toString())
        .claim("email", credential.getEmail())
        .claim("role", credential.getRole())
        .setIssuedAt(new Date())
        // Token expires in 30 days
        .setExpiration(new Date(System.currentTimeMillis() + 1000L * 60 * 60 * 24 * 30))
        .signWith(getSigningKey(), SignatureAlgorithm.HS256)
        .compact();
  }

  // Translates your plain Base64 string into a secure HMAC SHA key
  private Key getSigningKey() {
    byte[] keyBytes = Decoders.BASE64.decode(secretKey);
    return Keys.hmacShaKeyFor(keyBytes);
  }
}