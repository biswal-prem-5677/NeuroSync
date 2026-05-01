package com.priya.neurosyncdemo.api;

import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.rekognition.RekognitionClient;
import software.amazon.awssdk.services.rekognition.model.Attribute;
import software.amazon.awssdk.services.rekognition.model.DetectFacesRequest;
import software.amazon.awssdk.services.rekognition.model.DetectFacesResponse;
import software.amazon.awssdk.services.rekognition.model.Emotion;
import software.amazon.awssdk.services.rekognition.model.Image;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Emotion API backed by AWS Rekognition.
 * - Supports mock mode via env var NEUROSYNC_MOCK_EMOTION or -Dneurosync.mock=HAPPY
 * - Defaults region from environment if null is passed.
 */
public class EmotionAPI implements AutoCloseable {
    private final RekognitionClient client;

    public EmotionAPI(Region region) {
        // If caller passes null, pick up default region from env/profile (or use a safe default).
        Region effective = (region != null) ? region
                : Region.of(System.getenv().getOrDefault("AWS_REGION",
                System.getProperty("aws.region", "ap-south-1")));
        this.client = RekognitionClient.builder().region(effective).build();
    }

    /** Convenience overload for file paths. */
    public String detectTopEmotion(Path imagePath) throws Exception {
        byte[] bytes = Files.readAllBytes(imagePath);
        return detectTopEmotion(bytes);
    }

    /** Returns only the top emotion label (kept for backward-compat). */
    public String detectTopEmotion(byte[] jpegBytes) throws Exception {
        EmotionResult r = detectAllEmotions(jpegBytes);
        return r.topEmotion();
    }

    /** New: full result (top label + confidence + all per-emotion scores). */
    public EmotionResult detectAllEmotions(Path imagePath) throws Exception {
        byte[] bytes = Files.readAllBytes(imagePath);
        return detectAllEmotions(bytes);
    }

    public EmotionResult detectAllEmotions(byte[] jpegBytes) throws Exception {
        // ---- Mock mode (useful for demos without AWS credentials) ----
        String mock = System.getenv("NEUROSYNC_MOCK_EMOTION");
        if (mock == null || mock.isBlank()) mock = System.getProperty("neurosync.mock");
        if (mock != null && !mock.isBlank()) {
            String label = mock.trim().toUpperCase();
            return new EmotionResult(label, 99.0, Map.of(label, 99.0));
        }

        // ---- Real call to Rekognition ----
        Image img = Image.builder().bytes(SdkBytes.fromByteArray(jpegBytes)).build();
        DetectFacesRequest req = DetectFacesRequest.builder()
                .image(img)
                .attributes(Attribute.ALL)
                .build();
        DetectFacesResponse resp = client.detectFaces(req);

        if (resp.faceDetails() == null || resp.faceDetails().isEmpty()) {
            return new EmotionResult("NoFace", null, Map.of());
        }

        List<Emotion> emotions = resp.faceDetails().get(0).emotions();
        if (emotions == null || emotions.isEmpty()) {
            return new EmotionResult("Unknown", null, Map.of());
        }

        Map<String, Double> scores = new HashMap<>();
        for (Emotion e : emotions) {
            if (e.typeAsString() != null && e.confidence() != null) {
                scores.put(e.typeAsString().toUpperCase(), e.confidence().doubleValue());
            }
        }

        Emotion top = emotions.stream().max(Comparator.comparing(Emotion::confidence)).orElse(null);
        if (top == null) {
            return new EmotionResult("Unknown", null, scores);
        }
        return new EmotionResult(top.typeAsString().toUpperCase(),
                top.confidence() == null ? null : top.confidence().doubleValue(),
                scores);
    }

    @Override
    public void close() {
        try { client.close(); } catch (Exception ignored) {}
    }
}
