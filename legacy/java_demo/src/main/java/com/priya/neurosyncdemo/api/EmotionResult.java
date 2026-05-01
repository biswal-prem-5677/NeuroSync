package com.priya.neurosyncdemo.api;

import java.util.Map;

public record EmotionResult(
        String topEmotion,
        Double topConfidence,
        Map<String, Double> scores  // e.g. HAPPY->97.5, SAD->1.2, ...
) {}
