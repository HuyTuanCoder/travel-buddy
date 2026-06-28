package travelbuddy.apigateway.controller;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@RestController
public class AiStreamController {

    private final HttpClient httpClient;
    private final ExecutorService executorService;

    public AiStreamController() {
        this.httpClient = HttpClient.newHttpClient();
        this.executorService = Executors.newCachedThreadPool();
    }

    // Use a unique prefix to bypass the spring-cloud-gateway-mvc catch-all route for /ai/**
    @GetMapping(value = "/api/v1/ai-stream/chat/{tripId}/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamChat(@PathVariable("tripId") String tripId) {
        System.out.println("Gateway: Received request for SSE stream: " + tripId);
        
        // 10 minutes timeout
        SseEmitter emitter = new SseEmitter(600000L);
        
        executorService.execute(() -> {
            try {
                HttpClient client = HttpClient.newBuilder()
                        .version(HttpClient.Version.HTTP_1_1)
                        .build();
                
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create("http://ai-agent-fastapi:8007/ai/chat/" + tripId + "/stream"))
                        .GET()
                        .build();

                System.out.println("Gateway: Proxying SSE to FastAPI...");
                HttpResponse<java.io.InputStream> response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());
                
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(response.body()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("data: ")) {
                            String payload = line.substring(6);
                            System.out.println("Gateway: Forwarding chunk: " + payload);
                            emitter.send(payload);
                            
                            // Check if this is the final token indicating completion
                            if (payload.contains("\"type\": \"done\"") || payload.contains("\"type\":\"done\"")) {
                                System.out.println("Gateway: Received done event, completing emitter");
                                emitter.complete();
                                break;
                            }
                        } else if (line.startsWith(": heartbeat")) {
                            emitter.send(SseEmitter.event().comment("heartbeat"));
                        }
                    }
                }
                emitter.complete();
            } catch (Exception e) {
                System.err.println("Gateway: SSE Stream Error: " + e.getMessage());
                emitter.completeWithError(e);
            }
        });

        emitter.onCompletion(() -> System.out.println("Gateway: SSE Emitter completed"));
        emitter.onTimeout(() -> System.out.println("Gateway: SSE Emitter timed out"));
        emitter.onError(e -> System.err.println("Gateway: SSE Emitter error: " + e.getMessage()));

        return emitter;
    }
}
