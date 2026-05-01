package com.priya.neurosyncdemo.service;

import java.util.LinkedHashMap;
import java.util.Map;

public class AnalyticsService {
    public Map<String,Integer> distributionForSession(long sessionId) throws Exception {
        try (var c = Db.get();
             var ps = c.prepareStatement("""
                 SELECT COALESCE(derived_emotion, top_emotion) e, COUNT(*) cnt
                 FROM emotion_events
                 WHERE session_id=?
                 GROUP BY e
                 ORDER BY cnt DESC
             """)) {
            ps.setLong(1, sessionId);
            try (var rs = ps.executeQuery()) {
                var out = new LinkedHashMap<String,Integer>();
                while (rs.next()) out.put(rs.getString(1), rs.getInt(2));
                return out;
            }
        }
    }

    public Map<Long,Double> confidenceTimeline(long sessionId) throws Exception {
        try (var c = Db.get();
             var ps = c.prepareStatement("""
                 SELECT ts, confidence FROM emotion_events
                 WHERE session_id=? ORDER BY ts
             """)) {
            ps.setLong(1, sessionId);
            try (var rs = ps.executeQuery()) {
                var out = new LinkedHashMap<Long,Double>();
                while (rs.next()) out.put(rs.getLong(1), rs.getDouble(2));
                return out;
            }
        }
    }
}
