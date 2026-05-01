package com.priya.neurosyncdemo.core;

import com.priya.neurosyncdemo.api.EmotionResult;

public class EmotionMapper {
    // minimal heuristics; refine later
    public static String derivedLabel(EmotionResult r) {
        String top = r.topEmotion()==null? "UNKNOWN" : r.topEmotion().toUpperCase();
        double c = r.topConfidence()==null?0:r.topConfidence();

        return switch (top) {
            case "CALM" -> (c < 60 ? "SLEEPY" : "CONFIDENT");
            case "HAPPY" -> (c > 85 ? "EXCITED" : "CONFIDENT");
            case "CONFUSED" -> (c > 70 ? "FRUSTRATED" : "DOUBTFUL");
            case "FEAR" -> "NERVOUS";
            case "DISGUSTED" -> "DISGUST";
            case "SURPRISED" -> (c > 75 ? "ANTICIPATION" : "SURPRISED");
            case "SAD" -> (c > 70 ? "BORED" : "SAD");
            case "ANGRY" -> "FRUSTRATED";
            default -> "NEUTRAL";
        };
    }
}
