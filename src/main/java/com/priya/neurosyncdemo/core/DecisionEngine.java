package com.priya.neurosyncdemo.core;

public class DecisionEngine {
    public static String actionForDerived(String label) {
        if (label == null) return "Continue at current pace.";
        return switch (label.toUpperCase()) {
            case "SLEEPY" -> "Insert a 1-min energizer clip; reduce difficulty briefly.";
            case "BORED" -> "Increase interactivity: switch to a quick quiz or challenge.";
            case "NERVOUS" -> "Offer step-by-step hint mode; reassure with examples.";
            case "CONFIDENT" -> "Advance to next level with a tougher problem.";
            case "EXCITED" -> "Introduce bonus problem; award points.";
            case "ANTICIPATION" -> "Reveal next concept teaser with mini-quiz.";
            case "FRUSTRATED" -> "Show guided solution; add optional break.";
            case "DOUBTFUL" -> "Provide clarifying summary and concept checks.";
            case "DISGUST" -> "Switch example context; reduce complexity.";
            case "NEUTRAL" -> "Keep steady pace; quick comprehension check.";
            default -> "Continue at current pace.";
        };
    }

    public static String courseComment(double positivePct) {
        if (positivePct >= 0.7) return "You are doing great in this course!";
        if (positivePct >= 0.5) return "Good progress; keep practicing.";
        return "You should focus more on this course.";
    }
}
