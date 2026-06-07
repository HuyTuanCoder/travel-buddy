package com.travelbuddy.itineraryservice.grpc;

import com.travelbuddy.location.grpc.GetPlacesBatchRequest;
import com.travelbuddy.location.grpc.GetPlacesBatchResponse;
import com.travelbuddy.location.grpc.LocationGrpcServiceGrpc;
import com.travelbuddy.location.grpc.PlaceInfo;
import net.devh.boot.grpc.client.inject.GrpcClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;
import java.util.Map;

@Service
public class LocationGrpcClient {

  private static final Logger log = LoggerFactory.getLogger(LocationGrpcClient.class);

  // Matches the gRPC server name configured in application.yml
  @GrpcClient("location-service")
  private LocationGrpcServiceGrpc.LocationGrpcServiceBlockingStub locationStub;

  /**
   * Batch fetches place information from the Location Service via gRPC.
   *
   * @param googlePlaceIds List of Google Place IDs to fetch.
   * @return A map where the key is the Google Place ID and the value is the PlaceInfo.
   */
  public Map<String, PlaceInfo> fetchPlaces(List<String> googlePlaceIds) {
    if (googlePlaceIds == null || googlePlaceIds.isEmpty()) {
      return Collections.emptyMap();
    }

    log.info("[gRPC Client] Requesting batch fetch for {} places", googlePlaceIds.size());

    try {
      GetPlacesBatchRequest request = GetPlacesBatchRequest.newBuilder()
          .addAllGooglePlaceIds(googlePlaceIds)
          .build();

      GetPlacesBatchResponse response = locationStub.getPlacesBatch(request);

      Map<String, PlaceInfo> placesMap = response.getPlacesMap();
      log.info("[gRPC Client] Received {} places from Location Service", placesMap.size());
      
      return placesMap;

    } catch (Exception e) {
      log.error("[gRPC Client] Failed to fetch places via gRPC: {}", e.getMessage(), e);
      // Graceful degradation: return empty map so the itinerary can still load (just without map data)
      return Collections.emptyMap();
    }
  }
}
