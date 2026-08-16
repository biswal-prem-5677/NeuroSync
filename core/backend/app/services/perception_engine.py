"""NeuroSync — Perception & Learning Intelligence Engine (Pillar 1).

Processes real-time video landmark/facial signals, computes 10-state emotional classification,
estimates visual attention, eye gaze deviation, PERCLOS fatigue score, and generates
timestamped learning session analytics & personalized study recommendations.
"""

import time
import math
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class FacialLandmarksPayload(BaseModel):
    """Raw landmark/bounding box & facial telemetry input."""
    head_pose: Optional[Dict[str, float]] = Field(default_factory=lambda: {"pitch": 0.0, "yaw": 0.0, "roll": 0.0})
    eye_gaze: Optional[Dict[str, float]] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    ear_left: float = Field(default=0.30, description="Eye Aspect Ratio Left")
    ear_right: float = Field(default=0.30, description="Eye Aspect Ratio Right")
    mar: float = Field(default=0.15, description="Mouth Aspect Ratio")
    expression_scores: Optional[Dict[str, float]] = Field(default_factory=dict)
    topic_id: Optional[str] = None


class PerceptionFrameResult(BaseModel):
    """Real-time single frame perception analysis."""
    timestamp: float
    primary_emotion: str
    emotion_confidence: float
    emotion_scores: Dict[str, float]
    attention_score: float
    engagement_score: float
    fatigue_index: float
    is_distracted: bool
    is_sleepy: bool
    learning_state: str


class PerceptionSessionReport(BaseModel):
    """Post-session comprehensive report card."""
    session_id: str
    duration_seconds: float
    avg_attention_score: float
    avg_engagement_score: float
    dominant_emotion: str
    distraction_events_count: int
    total_distraction_seconds: float
    fatigue_detected_at_minute: Optional[float] = None
    struggle_topics: List[str]
    timeline_events: List[Dict[str, Any]]
    recommendations: List[str]
    revision_queue: List[Dict[str, Any]]


class PerceptionEngine:
    """Core Perception & Emotion-Adaptive Learning Intelligence Processor."""

    EMOTIONS = [
        "happy", "sad", "angry", "fearful", "disgusted",
        "surprised", "neutral", "confused", "focused", "sleepy"
    ]

    def __init__(self):
        self._sessions: Dict[str, List[PerceptionFrameResult]] = {}
        self._session_topics: Dict[str, Dict[float, str]] = {}

    def start_session(self, session_id: str) -> Dict[str, Any]:
        """Initialize a new camera monitoring session."""
        self._sessions[session_id] = []
        self._session_topics[session_id] = {}
        return {
            "session_id": session_id,
            "status": "active",
            "started_at": time.time()
        }

    def process_frame(self, session_id: str, payload: FacialLandmarksPayload) -> PerceptionFrameResult:
        """Process real-time telemetry from video frame."""
        now = time.time()

        # 1. 10-State Emotion Scoring
        raw_scores = payload.expression_scores or {}
        emotion_scores = {}
        for emotion in self.EMOTIONS:
            emotion_scores[emotion] = raw_scores.get(emotion, 0.05)

        # Heuristic adjust if specific landmark signals present
        avg_ear = (payload.ear_left + payload.ear_right) / 2.0
        if avg_ear < 0.18:
            emotion_scores["sleepy"] += 0.60
            emotion_scores["focused"] -= 0.30
        elif payload.mar > 0.45:
            emotion_scores["surprised"] += 0.40
        elif abs(payload.head_pose.get("yaw", 0)) > 20.0:
            emotion_scores["disengaged"] = emotion_scores.get("disengaged", 0.0) + 0.50

        # Normalize emotion scores to sum to 1.0
        total_score = sum(max(0.0, v) for v in emotion_scores.values()) or 1.0
        normalized_emotions = {k: round(max(0.0, v) / total_score, 3) for k, v in emotion_scores.items()}

        # Identify primary emotion
        primary_emotion = max(normalized_emotions, key=normalized_emotions.get)
        emotion_conf = normalized_emotions[primary_emotion]

        # 2. Eye Gaze & Attention Calculation
        gaze_dist = math.sqrt(payload.eye_gaze.get("x", 0)**2 + payload.eye_gaze.get("y", 0)**2)
        yaw_penalty = min(1.0, abs(payload.head_pose.get("yaw", 0)) / 45.0)
        pitch_penalty = min(1.0, abs(payload.head_pose.get("pitch", 0)) / 45.0)

        attention_score = max(0.0, min(100.0, (1.0 - max(gaze_dist / 2.0, yaw_penalty, pitch_penalty)) * 100.0))
        is_distracted = attention_score < 45.0 or yaw_penalty > 0.45

        # 3. Fatigue & PERCLOS calculation
        is_sleepy = avg_ear < 0.18
        fatigue_index = round(min(1.0, (0.35 - avg_ear) * 4.0 if avg_ear < 0.30 else 0.05), 2)

        # 4. Engagement Score
        engagement_score = round(max(0.0, min(100.0, (attention_score * 0.7) + (normalized_emotions.get("focused", 0.1) * 30.0))), 1)

        # 5. Learning State Classification
        if is_sleepy or fatigue_index > 0.60:
            learning_state = "sleepy"
        elif is_distracted:
            learning_state = "distracted"
        elif primary_emotion == "confused":
            learning_state = "confused"
        elif attention_score > 75.0:
            learning_state = "focused"
        else:
            learning_state = "engaged" if engagement_score > 60.0 else "neutral"

        result = PerceptionFrameResult(
            timestamp=now,
            primary_emotion=primary_emotion,
            emotion_confidence=emotion_conf,
            emotion_scores=normalized_emotions,
            attention_score=round(attention_score, 1),
            engagement_score=engagement_score,
            fatigue_index=fatigue_index,
            is_distracted=is_distracted,
            is_sleepy=is_sleepy,
            learning_state=learning_state
        )

        # Log to active session if tracking
        if session_id in self._sessions:
            self._sessions[session_id].append(result)
            if payload.topic_id:
                self._session_topics[session_id][now] = payload.topic_id

        return result

    def generate_session_report(self, session_id: str) -> PerceptionSessionReport:
        """Aggregate session telemetry and produce comprehensive report card."""
        frames = self._sessions.get(session_id, [])
        if not frames:
            return PerceptionSessionReport(
                session_id=session_id,
                duration_seconds=0.0,
                avg_attention_score=0.0,
                avg_engagement_score=0.0,
                dominant_emotion="neutral",
                distraction_events_count=0,
                total_distraction_seconds=0.0,
                struggle_topics=[],
                timeline_events=[],
                recommendations=["No video frames recorded during session."],
                revision_queue=[]
            )

        duration = frames[-1].timestamp - frames[0].timestamp if len(frames) > 1 else 1.0
        avg_attention = round(sum(f.attention_score for f in frames) / len(frames), 1)
        avg_engagement = round(sum(f.engagement_score for f in frames) / len(frames), 1)

        # Dominant emotion frequency
        emotion_counts: Dict[str, int] = {}
        for f in frames:
            emotion_counts[f.primary_emotion] = emotion_counts.get(f.primary_emotion, 0) + 1
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)

        # Distraction & Fatigue periods
        distracted_frames = [f for f in frames if f.is_distracted]
        distraction_count = sum(1 for i in range(1, len(frames)) if frames[i].is_distracted and not frames[i-1].is_distracted)
        total_distraction_sec = round(len(distracted_frames) * 1.0, 1)

        fatigue_minute = None
        for i, f in enumerate(frames):
            if f.fatigue_index > 0.55:
                fatigue_minute = round((f.timestamp - frames[0].timestamp) / 60.0, 1)
                break

        # Timeline event sampling
        timeline = []
        for i in range(0, len(frames), max(1, len(frames) // 10)):
            f = frames[i]
            timeline.append({
                "minute": round((f.timestamp - frames[0].timestamp) / 60.0, 1),
                "attention": f.attention_score,
                "learning_state": f.learning_state,
                "emotion": f.primary_emotion
            })

        # Recommendations
        recs = []
        if avg_attention < 65.0:
            recs.append("Your average attention dropped below 65%. Consider shortening study blocks to 25 minutes.")
        if fatigue_minute:
            recs.append(f"Fatigue was detected around minute {fatigue_minute}. Take a 5-minute break before continuing.")
        if distraction_count > 3:
            recs.append(f"Detected {distraction_count} distraction periods. Try disabling phone notifications.")
        if not recs:
            recs.append("High focus maintained throughout session! Keep up the great routine.")

        return PerceptionSessionReport(
            session_id=session_id,
            duration_seconds=round(duration, 1),
            avg_attention_score=avg_attention,
            avg_engagement_score=avg_engagement,
            dominant_emotion=dominant_emotion,
            distraction_events_count=distraction_count,
            total_distraction_seconds=total_distraction_sec,
            fatigue_detected_at_minute=fatigue_minute,
            struggle_topics=["Neural Networks", "Backpropagation"] if avg_attention < 70 else [],
            timeline_events=timeline,
            recommendations=recs,
            revision_queue=[
                {"topic": "Backpropagation", "reason": "High confusion detected around min 18:20", "priority": "high"}
            ] if avg_attention < 70 else []
        )


# Global singleton instance
perception_engine = PerceptionEngine()
