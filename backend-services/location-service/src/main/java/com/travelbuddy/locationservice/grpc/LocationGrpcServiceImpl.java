package com.travelbuddy.locationservice.grpc;

import com.travelbuddy.location.grpc.GetPlacesBatchRequest;
import com.travelbuddy.location.grpc.GetPlacesBatchResponse;
import com.travelbuddy.location.grpc.AddLocationRequest;
import com.travelbuddy.location.grpc.AddLocationResponse;
import com.travelbuddy.location.grpc.LocationGrpcServiceGrpc;
import com.travelbuddy.location.grpc.PlaceInfo;
import com.travelbuddy.locationservice.model.Place;
import com.travelbuddy.locationservice.service.PlaceService;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

@GrpcService
public class LocationGrpcServiceImpl extends LocationGrpcServiceGrpc.LocationGrpcServiceImplBase {

  private static final Logger log = LoggerFactory.getLogger(LocationGrpcServiceImpl.class);

  private final PlaceService placeService;

  public LocationGrpcServiceImpl(PlaceService placeService) {
    this.placeService = placeService;
  }

  @Override
  public void getPlacesBatch(GetPlacesBatchRequest request, StreamObserver<GetPlacesBatchResponse> responseObserver) {
    log.info("[gRPC Server] Received batch request for {} places", request.getGooglePlaceIdsCount());

    try {
      // 1. Fetch from our self-healing service
      List<String> requestedIds = request.getGooglePlaceIdsList();
      List<Place> places = placeService.getPlacesBatch(requestedIds);

      // 2. Build the map response
      GetPlacesBatchResponse.Builder responseBuilder = GetPlacesBatchResponse.newBuilder();

      for (Place place : places) {
        PlaceInfo info = PlaceInfo.newBuilder()
            .setGooglePlaceId(place.getGooglePlaceId())
            .setName(place.getName())
            .setFormattedAddress(place.getFormattedAddress() != null ? place.getFormattedAddress() : "")
            .setLatitude(place.getLatitude())
            .setLongitude(place.getLongitude())
            .setPhotoReference(place.getPhotoReference() != null ? place.getPhotoReference() : "")
            .setPlaceTypes(place.getPlaceTypes() != null ? place.getPlaceTypes() : "")
            .build();

        responseBuilder.putPlaces(place.getGooglePlaceId(), info);
      }

      // 3. Send response back to the client
      GetPlacesBatchResponse response = responseBuilder.build();
      responseObserver.onNext(response);
      responseObserver.onCompleted();

      log.info("[gRPC Server] Successfully returned {} places", response.getPlacesCount());

    } catch (Exception e) {
      log.error("[gRPC Server] Error processing batch request", e);
      responseObserver.onError(io.grpc.Status.INTERNAL
          .withDescription(e.getMessage())
          .withCause(e)
          .asRuntimeException());
    }
  }

  @Override
  public void addLocation(AddLocationRequest request, StreamObserver<AddLocationResponse> responseObserver) {
    String placeId = request.getGooglePlaceId();
    log.info("[gRPC Server] Received addLocation request for placeId: {}", placeId);

    try {
      Place place = placeService.addPlace(placeId);
      
      PlaceInfo info = PlaceInfo.newBuilder()
          .setGooglePlaceId(place.getGooglePlaceId())
          .setName(place.getName())
          .setFormattedAddress(place.getFormattedAddress() != null ? place.getFormattedAddress() : "")
          .setLatitude(place.getLatitude())
          .setLongitude(place.getLongitude())
          .setPhotoReference(place.getPhotoReference() != null ? place.getPhotoReference() : "")
          .setPlaceTypes(place.getPlaceTypes() != null ? place.getPlaceTypes() : "")
          .build();
          
      AddLocationResponse response = AddLocationResponse.newBuilder()
          .setPlace(info)
          .build();
          
      responseObserver.onNext(response);
      responseObserver.onCompleted();
      
      log.info("[gRPC Server] Successfully registered place {}", placeId);
    } catch (Exception e) {
      log.error("[gRPC Server] Error processing addLocation request", e);
      responseObserver.onError(io.grpc.Status.INTERNAL
          .withDescription(e.getMessage())
          .withCause(e)
          .asRuntimeException());
    }
  }
}
