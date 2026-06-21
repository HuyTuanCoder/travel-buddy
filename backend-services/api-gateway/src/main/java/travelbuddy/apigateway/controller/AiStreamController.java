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

    @GetMapping(value = "/ai/chat/{tripId}/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamChat(@PathVariable("tripId") String tripId) {
        // Set timeout to 30 minutes
        SseEmitter emitter = new SseEmitter(1800000L);
        
        executorService.execute(() -> {
            try {
                // Connect directly to the downstream FastAPI service
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create("http://ai-agent-fastapi:8007/ai/chat/" + tripId + "/stream"))
                        .GET()
                        .build();

                // Send request and get response stream
                HttpResponse<java.io.InputStream> response = httpClient.send(request, HttpResponse.BodyHandlers.ofInputStream());
                
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(response.body()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("data: ")) {
                            // Extract the actual JSON payload since SseEmitter wraps it in "data: " again
                            String payload = line.substring(6);
                            emitter.send(payload);
                        }
                    }
                }
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }
}
