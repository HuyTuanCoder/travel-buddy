package com.travelbuddy.locationservice.client;

import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;
import com.travelbuddy.locationservice.exception.GooglePlacesApiException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/**
 * Lightweight wrapper around the Google Places API.
 * Uses RestClient (Spring 7) to call Place Details and extract only the fields we need.
 *
 * Billing: We request only "Basic" tier fields (name, address, geometry, photos, types)
 * which costs $0.017/call instead of $0.032 for "Contact" tier fields.
 */
@Component
public class GooglePlacesClient {

  private static final Logger log = LoggerFactory.getLogger(GooglePlacesClient.class);

  private static final String PLACE_DETAILS_URL =
      "https://maps.googleapis.com/maps/api/place/details/json";

  private static final String REQUESTED_FIELDS =
      "name,formatted_address,geometry/location,photos,types";

  private final RestClient restClient;
  private final ObjectMapper objectMapper;
  private final String apiKey;

  public GooglePlacesClient(@Value("${google.maps.api-key}") String apiKey) {
    this.restClient = RestClient.create();
    this.objectMapper = new ObjectMapper();
    this.apiKey = apiKey;
  }

  // ==================== Public API ====================

  /**
   * Fetches place details from Google Maps for a given placeId.
   * Returns a parsed result, or throws RuntimeException on failure.
   */
  public PlaceDetailsResult fetchPlaceDetails(String googlePlaceId) {
    log.info("[GooglePlacesClient] Fetching details for placeId={}", googlePlaceId);

    String responseBody = restClient.get()
        .uri(PLACE_DETAILS_URL + "?place_id={placeId}&fields={fields}&key={key}",
            googlePlaceId, REQUESTED_FIELDS, apiKey)
        .retrieve()
        .body(String.class);

    return parseResponse(responseBody, googlePlaceId);
  }

  // ==================== Internal ====================

  private PlaceDetailsResult parseResponse(String json, String googlePlaceId) {
    try {
      JsonNode root = objectMapper.readTree(json);
      String status = root.path("status").asText();

      if (!"OK".equals(status)) {
        throw new GooglePlacesApiException(
            "Google Places API returned status=" + status + " for placeId=" + googlePlaceId);
      }

      JsonNode result = root.path("result");

      String name = result.path("name").asText("");
      String formattedAddress = result.path("formatted_address").asText("");

      JsonNode location = result.path("geometry").path("location");
      double lat = location.path("lat").asDouble();
      double lng = location.path("lng").asDouble();

      // Extract the first photo reference if available
      String photoReference = null;
      JsonNode photos = result.path("photos");
      if (photos.isArray() && !photos.isEmpty()) {
        photoReference = photos.get(0).path("photo_reference").asText(null);
      }

      // Flatten types array into comma-separated string
      String placeTypes = null;
      JsonNode types = result.path("types");
      if (types.isArray() && !types.isEmpty()) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < types.size(); i++) {
          if (i > 0) sb.append(",");
          sb.append(types.get(i).asText());
        }
        placeTypes = sb.toString();
      }

      log.info("[GooglePlacesClient] Parsed: name='{}', lat={}, lng={}", name, lat, lng);
      return new PlaceDetailsResult(name, formattedAddress, lat, lng, photoReference, placeTypes);

    } catch (GooglePlacesApiException e) {
      throw e;
    } catch (Exception e) {
      throw new GooglePlacesApiException(
          "Failed to parse Google Places response for placeId=" + googlePlaceId, e);
    }
  }

  // ==================== Inner Result Class ====================

  /**
   * Simple data carrier for parsed Google Places API response.
   */
  public static class PlaceDetailsResult {
    private final String name;
    private final String formattedAddress;
    private final double latitude;
    private final double longitude;
    private final String photoReference;
    private final String placeTypes;

    public PlaceDetailsResult(String name, String formattedAddress,
                               double latitude, double longitude,
                               String photoReference, String placeTypes) {
      this.name = name;
      this.formattedAddress = formattedAddress;
      this.latitude = latitude;
      this.longitude = longitude;
      this.photoReference = photoReference;
      this.placeTypes = placeTypes;
    }

    public String getName() { return name; }
    public String getFormattedAddress() { return formattedAddress; }
    public double getLatitude() { return latitude; }
    public double getLongitude() { return longitude; }
    public String getPhotoReference() { return photoReference; }
    public String getPlaceTypes() { return placeTypes; }
  }
}
