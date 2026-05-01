package com.priya.neurosyncdemo.service;

public class PointsService {
    public void award(String userId, int delta, String reason) throws Exception {
        try (var c = Db.get();
             var ps = c.prepareStatement("""
               INSERT INTO points_ledger(user_id, delta, reason, ts)
               VALUES(?,?,?,?)
             """)) {
            ps.setString(1, userId);
            ps.setInt(2, delta);
            ps.setString(3, reason);
            ps.setLong(4, System.currentTimeMillis());
            ps.executeUpdate();
        }
    }

    public int balance(String userId) throws Exception {
        try (var c = Db.get();
             var ps = c.prepareStatement("""
               SELECT COALESCE(SUM(delta),0) FROM points_ledger WHERE user_id=?
             """)) {
            ps.setString(1, userId);
            try (var rs = ps.executeQuery()) { return rs.next()? rs.getInt(1) : 0; }
        }
    }
}
