package com.priya.neurosyncdemo.store;

import com.priya.neurosyncdemo.service.Db;
import java.util.ArrayList;
import java.util.List;

public class EnrollmentStore {
    public void enroll(String userId, String courseId) throws Exception {
        try (var c = Db.get();
             var ps = c.prepareStatement("""
                 INSERT IGNORE INTO enrollments(user_id,course_id) VALUES(?,?)
             """)) {
            ps.setString(1, userId);
            ps.setString(2, courseId);
            ps.executeUpdate();
        }
    }

    public List<String[]> listForUser(String userId) throws Exception {
        try (var c = Db.get();
             var ps = c.prepareStatement("""
                SELECT c.id, c.title
                FROM enrollments e JOIN courses c ON e.course_id=c.id
                WHERE e.user_id=?
                ORDER BY c.title
             """)) {
            ps.setString(1, userId);
            try (var rs = ps.executeQuery()) {
                var out = new ArrayList<String[]>();
                while (rs.next()) out.add(new String[]{rs.getString(1), rs.getString(2)});
                return out;
            }
        }
    }
}
