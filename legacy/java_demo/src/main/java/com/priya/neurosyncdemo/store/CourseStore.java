package com.priya.neurosyncdemo.store;

import com.priya.neurosyncdemo.service.Db;
import java.util.ArrayList;
import java.util.List;

public class CourseStore {
    public void upsert(String courseId, String title) throws Exception {
        try (var c = Db.get();
             var ps = c.prepareStatement("""
                 INSERT INTO courses(id,title) VALUES(?,?)
                 ON DUPLICATE KEY UPDATE title=VALUES(title)
             """)) {
            ps.setString(1, courseId);
            ps.setString(2, title);
            ps.executeUpdate();
        }
    }

    public List<String[]> listAll() throws Exception {
        try (var c = Db.get(); var ps = c.prepareStatement("SELECT id,title FROM courses ORDER BY title");
             var rs = ps.executeQuery()) {
            var out = new ArrayList<String[]>();
            while (rs.next()) out.add(new String[]{rs.getString(1), rs.getString(2)});
            return out;
        }
    }

    public String titleOf(String courseId) throws Exception {
        try (var c = Db.get(); var ps = c.prepareStatement("SELECT title FROM courses WHERE id=?")) {
            ps.setString(1, courseId);
            try (var rs = ps.executeQuery()) { return rs.next()?rs.getString(1):null; }
        }
    }
}
