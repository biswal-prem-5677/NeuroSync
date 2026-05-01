package com.priya.neurosyncdemo.service;

import com.priya.neurosyncdemo.api.EmotionResult;
import java.sql.*;
import java.util.Map;

public class EmotionStore {


    // keep package + imports as-is
    public long createSession(String userId, String courseId, long startedAtMillis) throws Exception {
        if (userId == null || userId.isBlank()) {
            throw new IllegalArgumentException("User ID cannot be null or blank when creating a session");
        }

        // Insert both user_id and student_id to be compatible with older schema that still has student_id NOT NULL
        try (Connection c = Db.get();
             PreparedStatement ps = c.prepareStatement("""
            INSERT INTO sessions(user_id, student_id, course_id, started_at)
            VALUES(?,?,?,?)
         """, Statement.RETURN_GENERATED_KEYS)) {

            ps.setString(1, userId);          // user_id (new canonical)
            ps.setString(2, userId);          // student_id (legacy column kept for compatibility)
            ps.setString(3, courseId);
            ps.setLong(4, startedAtMillis);
            ps.executeUpdate();

            try (ResultSet rs = ps.getGeneratedKeys()) {
                if (rs.next()) return rs.getLong(1);
                throw new SQLException("Failed to retrieve generated session ID");
            }
        }
    }



    public void insertEmotionEvent(long sessionId, long tsMillis, String source,
                                   String derived, EmotionResult r) throws Exception {
        Map<String, Double> m = r.scores();

        try (Connection c = Db.get();
             PreparedStatement ps = c.prepareStatement("""
                INSERT INTO emotion_events(
                   session_id, ts, source, top_emotion, derived_emotion, confidence,
                   happy, sad, angry, calm, confused, surprised, disgusted, fear
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
             """)) {

            ps.setLong(1, sessionId);
            ps.setLong(2, tsMillis);
            ps.setString(3, source);
            ps.setString(4, r.topEmotion());
            ps.setString(5, derived);

            if (r.topConfidence() == null)
                ps.setNull(6, Types.DOUBLE);
            else
                ps.setDouble(6, r.topConfidence());

            ps.setObject(7,  m.getOrDefault("HAPPY", 0.0));
            ps.setObject(8,  m.getOrDefault("SAD", 0.0));
            ps.setObject(9,  m.getOrDefault("ANGRY", 0.0));
            ps.setObject(10, m.getOrDefault("CALM", 0.0));
            ps.setObject(11, m.getOrDefault("CONFUSED", 0.0));
            ps.setObject(12, m.getOrDefault("SURPRISED", 0.0));
            ps.setObject(13, m.getOrDefault("DISGUSTED", 0.0));
            ps.setObject(14, m.getOrDefault("FEAR", 0.0));

            ps.executeUpdate();
        }
    }
}
