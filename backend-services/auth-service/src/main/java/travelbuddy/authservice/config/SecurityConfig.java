package travelbuddy.authservice.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

  @Bean
  public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
        // Disable CSRF (Cross-Site Request Forgery)
        // CSRF protection is for session-based cookie logins. Since we use stateless JWTs, we don't need it.
        .csrf(AbstractHttpConfigurer::disable)

        // Configure Endpoint Rules
        .authorizeHttpRequests(auth -> auth
            // Leave the door completely open for login and registration
            .requestMatchers("/auth/login", "/auth/register").permitAll()
            // Any other endpoint in this service requires a valid token
            .anyRequest().authenticated()
        )

        // Tell Spring Security NEVER to create an HttpSession. Every single request must carry a JWT.
        .sessionManagement(session -> session
            .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
        );

    return http.build();
  }

  // This creates the BCrypt engine. Whenever you call passwordEncoder.encode("myPassword"),
  // it handles the salting and hashing automatically.
  @Bean
  public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
  }

  // We expose the AuthenticationManager bean here so we can grab it later
  // inside our AuthService to manually verify a user's login attempt.
  @Bean
  public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
    return config.getAuthenticationManager();
  }
}
