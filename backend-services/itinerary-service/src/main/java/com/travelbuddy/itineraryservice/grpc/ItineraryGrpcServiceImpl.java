package com.travelbuddy.itineraryservice.grpc;

import com.travelbuddy.itinerary.grpc.AddStopGrpcRequest;
import com.travelbuddy.itinerary.grpc.ItineraryGrpcServiceGrpc;
import com.travelbuddy.itinerary.grpc.StopTypeGrpc;
import com.travelbuddy.itinerary.grpc.TripStopGrpcResponse;
import com.travelbuddy.itineraryservice.dto.AddStopRequest;
import com.travelbuddy.itineraryservice.dto.TripStopResponse;
import com.travelbuddy.itineraryservice.model.StopType;
import com.travelbuddy.itineraryservice.service.TimelineService;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.math.BigDecimal;
import java.time.LocalTime;
import java.util.UUID;

@GrpcService
public class ItineraryGrpcServiceImpl extends ItineraryGrpcServiceGrpc.ItineraryGrpcServiceImplBase {

    private static final Logger log = LoggerFactory.getLogger(ItineraryGrpcServiceImpl.class);
    private final TimelineService timelineService;

    public ItineraryGrpcServiceImpl(TimelineService timelineService) {
        this.timelineService = timelineService;
    }

    @Override
    public void addStop(AddStopGrpcRequest request, StreamObserver<TripStopGrpcResponse> responseObserver) {
        log.info("[gRPC Server] Received AddStop command for DayId: {}", request.getDayId());

        try {
            // 1. Map gRPC Request to Java DTO exactly like the Controller does
            AddStopRequest dto = new AddStopRequest();
            dto.setGooglePlaceId(request.getGooglePlaceId());
            
            if (request.getStopType() != StopTypeGrpc.UNKNOWN && request.getStopType() != StopTypeGrpc.UNRECOGNIZED) {
                dto.setStopType(StopType.valueOf(request.getStopType().name()));
            }

            if (!request.getArrivalTime().isEmpty()) dto.setArrivalTime(LocalTime.parse(request.getArrivalTime()));
            if (!request.getDepartureTime().isEmpty()) dto.setDepartureTime(LocalTime.parse(request.getDepartureTime()));
            if (!request.getEstimatedCost().isEmpty()) dto.setEstimatedCost(new BigDecimal(request.getEstimatedCost()));
            if (!request.getUserNotes().isEmpty()) dto.setUserNotes(request.getUserNotes());

            // 2. Execute business logic
            UUID dayId = UUID.fromString(request.getDayId());
            TripStopResponse result = timelineService.addStop(dayId, dto, request.getUserId());

            // 3. Map Java DTO back to gRPC Response
            TripStopGrpcResponse.Builder responseBuilder = TripStopGrpcResponse.newBuilder()
                    .setId(result.getId().toString())
                    .setGooglePlaceId(result.getGooglePlaceId())
                    .setVisitOrder(result.getVisitOrder() != null ? result.getVisitOrder() : 0);

            if (result.getStopType() != null) responseBuilder.setStopType(StopTypeGrpc.valueOf(result.getStopType().name()));
            if (result.getArrivalTime() != null) responseBuilder.setArrivalTime(result.getArrivalTime().toString());
            if (result.getDepartureTime() != null) responseBuilder.setDepartureTime(result.getDepartureTime().toString());
            if (result.getEstimatedCost() != null) responseBuilder.setEstimatedCost(result.getEstimatedCost().toString());
            if (result.getUserNotes() != null) responseBuilder.setUserNotes(result.getUserNotes());

            if (result.getLocationName() != null) responseBuilder.setLocationName(result.getLocationName());
            if (result.getAddress() != null) responseBuilder.setAddress(result.getAddress());
            if (result.getLatitude() != null) responseBuilder.setLatitude(result.getLatitude());
            if (result.getLongitude() != null) responseBuilder.setLongitude(result.getLongitude());
            if (result.getImageUrl() != null) responseBuilder.setImageUrl(result.getImageUrl());

            responseObserver.onNext(responseBuilder.build());
            responseObserver.onCompleted();

            log.info("[gRPC Server] Successfully processed AddStop for PlaceId: {}", result.getGooglePlaceId());

        } catch (Exception e) {
            log.error("[gRPC Server] Error adding stop via gRPC", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage())
                    .withCause(e)
                    .asRuntimeException());
        }
    }
}
