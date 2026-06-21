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
import java.util.Collections;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import jakarta.servlet.http.HttpServletRequestWrapper;

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
    if (path.startsWith("/auth") || path.matches("^/ai/chat/.*/stream$")) {
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
    String userId = null;
    try {
      jwtUtil.validateToken(token);
      userId = jwtUtil.extractUserId(token);
    } catch (Exception e) {
      // If expired or tampered with, kill the request right here
      response.sendError(HttpStatus.UNAUTHORIZED.value(), "Token is invalid or expired");
      return;
    }

    // 4. PASSED: Forward the request to the downstream microservice with X-User-Id
    MutableHttpServletRequest mutableRequest = new MutableHttpServletRequest(request);
    mutableRequest.putHeader("X-User-Id", userId);
    
    filterChain.doFilter(mutableRequest, response);
  }

  private static class MutableHttpServletRequest extends HttpServletRequestWrapper {
    private final Map<String, String> customHeaders;

    public MutableHttpServletRequest(HttpServletRequest request) {
      super(request);
      this.customHeaders = new HashMap<>();
    }

    public void putHeader(String name, String value) {
      this.customHeaders.put(name, value);
    }

    @Override
    public String getHeader(String name) {
      String headerValue = customHeaders.get(name);
      if (headerValue != null) {
        return headerValue;
      }
      return super.getHeader(name);
    }

    @Override
    public Enumeration<String> getHeaderNames() {
      List<String> names = Collections.list(super.getHeaderNames());
      names.addAll(customHeaders.keySet());
      return Collections.enumeration(names);
    }

    @Override
    public Enumeration<String> getHeaders(String name) {
      String customHeaderValue = customHeaders.get(name);
      if (customHeaderValue != null) {
        return Collections.enumeration(Collections.singletonList(customHeaderValue));
      }
      return super.getHeaders(name);
    }
  }
}