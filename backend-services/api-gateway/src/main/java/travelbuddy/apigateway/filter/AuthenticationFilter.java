package travelbuddy.apigateway.filter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import travelbuddy.apigateway.util.JwtUtil;

import java.io.IOException;

@Component
public class AuthenticationFilter extends OncePerRequestFilter {

  private final JwtUtil jwtUtil;

  public AuthenticationFilter(JwtUtil jwtUtil) {
    this.jwtUtil = jwtUtil;
  }

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
      throws ServletException, IOException {

    String path = request.getRequestURI();

    // 1. OPEN DOORS: Let Auth traffic through without a token
    if (path.startsWith("/auth")) {
      filterChain.doFilter(request, response);
      return;
    }

    // 2. CHECK HEADER: Make sure they actually sent an Authorization header
    String authHeader = request.getHeader(HttpHeaders.AUTHORIZATION);
    if (authHeader == null || !authHeader.startsWith("Bearer ")) {
      response.sendError(HttpStatus.UNAUTHORIZED.value(), "Missing or invalid Authorization header");
      return;
    }

    // 3. VALIDATE: Chop off "Bearer " and check the math
    String token = authHeader.substring(7);
    try {
      jwtUtil.validateToken(token);
    } catch (Exception e) {
      // If expired or tampered with, kill the request right here
      response.sendError(HttpStatus.UNAUTHORIZED.value(), "Token is invalid or expired");
      return;
    }

    // 4. PASSED: Forward the request to the downstream microservice
    filterChain.doFilter(request, response);
  }
}