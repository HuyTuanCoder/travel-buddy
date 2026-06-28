package com.travelbuddy.itineraryservice.grpc;

import com.travelbuddy.itinerary.grpc.*;
import com.travelbuddy.itineraryservice.dto.AddStopRequest;
import com.travelbuddy.itineraryservice.dto.UpdateStopRequest;
import com.travelbuddy.itineraryservice.dto.TripStopResponse;
import com.travelbuddy.itineraryservice.model.StopType;
import com.travelbuddy.itineraryservice.model.ItineraryDay;
import com.travelbuddy.itineraryservice.repository.ItineraryDayRepository;
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
    private final ItineraryDayRepository dayRepository;

    public ItineraryGrpcServiceImpl(TimelineService timelineService, ItineraryDayRepository dayRepository) {
        this.timelineService = timelineService;
        this.dayRepository = dayRepository;
    }

    private UUID resolveDayId(String tripId, int dayNumber) {
        return dayRepository.findByItineraryIdAndDayNumber(UUID.fromString(tripId), dayNumber)
                .map(ItineraryDay::getId)
                .orElseThrow(() -> new IllegalArgumentException("No day found for Trip " + tripId + " at Day " + dayNumber));
    }

    private TripStopGrpcResponse mapToGrpcResponse(TripStopResponse result) {
        TripStopGrpcResponse.Builder builder = TripStopGrpcResponse.newBuilder()
                .setId(result.getId().toString())
                .setGooglePlaceId(result.getGooglePlaceId() != null ? result.getGooglePlaceId() : "")
                .setVisitOrder(result.getVisitOrder() != null ? result.getVisitOrder() : 0);

        if (result.getStopType() != null) builder.setStopType(StopTypeGrpc.valueOf(result.getStopType().name()));
        if (result.getArrivalTime() != null) builder.setArrivalTime(result.getArrivalTime().toString());
        if (result.getDepartureTime() != null) builder.setDepartureTime(result.getDepartureTime().toString());
        if (result.getEstimatedCost() != null) builder.setEstimatedCost(result.getEstimatedCost().toString());
        if (result.getUserNotes() != null) builder.setUserNotes(result.getUserNotes());
        
        if (result.getLocationName() != null) builder.setLocationName(result.getLocationName());
        if (result.getAddress() != null) builder.setAddress(result.getAddress());
        if (result.getLatitude() != null) builder.setLatitude(result.getLatitude());
        if (result.getLongitude() != null) builder.setLongitude(result.getLongitude());
        if (result.getImageUrl() != null) builder.setImageUrl(result.getImageUrl());
        
        return builder.build();
    }

    @Override
    public void addStop(AddStopGrpcRequest request, StreamObserver<TripStopGrpcResponse> responseObserver) {
        log.info("[gRPC] AddStop for Trip: {}, Day: {}", request.getTripId(), request.getDayNumber());
        try {
            UUID dayId = resolveDayId(request.getTripId(), request.getDayNumber());
            
            AddStopRequest dto = new AddStopRequest();
            dto.setGooglePlaceId(request.getGooglePlaceId());
            if (request.getStopType() != StopTypeGrpc.UNKNOWN && request.getStopType() != StopTypeGrpc.UNRECOGNIZED) {
                dto.setStopType(StopType.valueOf(request.getStopType().name()));
            }
            if (!request.getArrivalTime().isEmpty()) dto.setArrivalTime(LocalTime.parse(request.getArrivalTime()));
            if (!request.getDepartureTime().isEmpty()) dto.setDepartureTime(LocalTime.parse(request.getDepartureTime()));
            if (!request.getEstimatedCost().isEmpty()) dto.setEstimatedCost(new BigDecimal(request.getEstimatedCost()));
            if (!request.getUserNotes().isEmpty()) dto.setUserNotes(request.getUserNotes());

            TripStopResponse result = timelineService.addStop(dayId, dto, request.getUserId());
            responseObserver.onNext(mapToGrpcResponse(result));
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("[gRPC] Error in AddStop", e);
            responseObserver.onError(io.grpc.Status.INTERNAL.withDescription(e.getMessage()).withCause(e).asRuntimeException());
        }
    }

    @Override
    public void removeStop(RemoveStopGrpcRequest request, StreamObserver<EmptyGrpcResponse> responseObserver) {
        log.info("[gRPC] RemoveStop for Stop: {}", request.getStopId());
        try {
            timelineService.removeStop(UUID.fromString(request.getStopId()), request.getUserId());
            responseObserver.onNext(EmptyGrpcResponse.newBuilder().setSuccess(true).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("[gRPC] Error in RemoveStop", e);
            responseObserver.onError(io.grpc.Status.INTERNAL.withDescription(e.getMessage()).withCause(e).asRuntimeException());
        }
    }

    @Override
    public void updateStop(UpdateStopGrpcRequest request, StreamObserver<TripStopGrpcResponse> responseObserver) {
        log.info("[gRPC] UpdateStop for Stop: {}", request.getStopId());
        try {
            UpdateStopRequest dto = new UpdateStopRequest();
            if (request.getStopType() != StopTypeGrpc.UNKNOWN && request.getStopType() != StopTypeGrpc.UNRECOGNIZED) {
                dto.setStopType(StopType.valueOf(request.getStopType().name()));
            }
            if (!request.getArrivalTime().isEmpty()) dto.setArrivalTime(LocalTime.parse(request.getArrivalTime()));
            if (!request.getDepartureTime().isEmpty()) dto.setDepartureTime(LocalTime.parse(request.getDepartureTime()));
            if (!request.getEstimatedCost().isEmpty()) dto.setEstimatedCost(new BigDecimal(request.getEstimatedCost()));
            if (!request.getUserNotes().isEmpty()) dto.setUserNotes(request.getUserNotes());

            TripStopResponse result = timelineService.updateStop(UUID.fromString(request.getStopId()), dto, request.getUserId());
            responseObserver.onNext(mapToGrpcResponse(result));
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("[gRPC] Error in UpdateStop", e);
            responseObserver.onError(io.grpc.Status.INTERNAL.withDescription(e.getMessage()).withCause(e).asRuntimeException());
        }
    }

    @Override
    public void moveStop(MoveStopGrpcRequest request, StreamObserver<TripStopGrpcResponse> responseObserver) {
        log.info("[gRPC] MoveStop for Stop: {} to Trip: {}, Day: {}", request.getStopId(), request.getTripId(), request.getTargetDayNumber());
        try {
            UUID targetDayId = resolveDayId(request.getTripId(), request.getTargetDayNumber());
            com.travelbuddy.itineraryservice.dto.MoveStopRequest moveReq = new com.travelbuddy.itineraryservice.dto.MoveStopRequest();
            moveReq.setTargetDayId(targetDayId);
            moveReq.setTargetVisitOrder(null);
            
            TripStopResponse result = timelineService.moveStop(UUID.fromString(request.getStopId()), moveReq, request.getUserId());
            responseObserver.onNext(mapToGrpcResponse(result));
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("[gRPC] Error in MoveStop", e);
            responseObserver.onError(io.grpc.Status.INTERNAL.withDescription(e.getMessage()).withCause(e).asRuntimeException());
        }
    }
}
