package com.priya.neurosyncdemo.store;

import com.priya.neurosyncdemo.service.Db;   // <- use the service Db
import org.mindrot.jbcrypt.BCrypt;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

/** User accounts + auth helpers. */
public class UserStore {

    // == Login by student id ==
    public boolean authenticateByStudentId(String studentId, String password) throws Exception {
        if (studentId == null || studentId.isBlank() || password == null) return false;
        try (Connection c = Db.get();
             PreparedStatement ps = c.prepareStatement("SELECT password_hash FROM users WHERE id=?")) {
            ps.setString(1, studentId.trim());
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) return false;
                return BCrypt.checkpw(password, rs.getString(1));
            }
        }
    }

    // == Login by email ==
    public boolean authenticateByEmail(String email, String password) throws Exception {
        if (email == null || email.isBlank() || password == null) return false;
        try (Connection c = Db.get();
             PreparedStatement ps = c.prepareStatement("SELECT password_hash FROM users WHERE email=?")) {
            ps.setString(1, email.trim().toLowerCase());
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) return false;
                return BCrypt.checkpw(password, rs.getString(1));
            }
        }
    }

    // == Lookup id by email (for FK safety when logging in via email) ==
    public String findIdByEmail(String email) throws Exception {
        if (email == null || email.isBlank()) return null;
        try (Connection c = Db.get();
             PreparedStatement ps = c.prepareStatement("SELECT id FROM users WHERE email=?")) {
            ps.setString(1, email.trim().toLowerCase());
            try (ResultSet rs = ps.executeQuery()) { return rs.next() ? rs.getString(1) : null; }
        }
    }

    // == Create/Upsert user (name, email, studentId, password) ==
    public boolean signUp(String name, String email, String studentId, String password) throws Exception {
        if (name == null || name.isBlank()) throw new IllegalArgumentException("Name is required");
        if (studentId == null || studentId.isBlank()) throw new IllegalArgumentException("Student ID is required");
        if (password == null || password.isBlank()) throw new IllegalArgumentException("Password is required");

        String em = (email == null || email.isBlank()) ? null : email.trim().toLowerCase();
        String hash = BCrypt.hashpw(password, BCrypt.gensalt(12));

        try (Connection c = Db.get();
             PreparedStatement ps = c.prepareStatement(
                     "INSERT INTO users(id, name, email, password_hash, created_at) VALUES(?,?,?,?,?) " +
                             "ON DUPLICATE KEY UPDATE name=VALUES(name), email=VALUES(email), password_hash=VALUES(password_hash)"
             )) {
            ps.setString(1, studentId.trim());
            ps.setString(2, name.trim());
            ps.setString(3, em);
            ps.setString(4, hash);
            ps.setLong(5, System.currentTimeMillis());
            ps.executeUpdate();
            return true;
        }
    }

    // == Change password ==
    public void changePassword(String userId, String oldPassword, String newPassword) throws Exception {
        if (userId == null || userId.isBlank()) throw new IllegalArgumentException("User ID required");
        if (newPassword == null || newPassword.isBlank()) throw new IllegalArgumentException("New password required");

        String currentHash;
        try (Connection c = Db.get();
             PreparedStatement ps = c.prepareStatement("SELECT password_hash FROM users WHERE id=?")) {
            ps.setString(1, userId.trim());
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) throw new IllegalStateException("User not found");
                currentHash = rs.getString(1);
            }
        }
        if (!BCrypt.checkpw(oldPassword == null ? "" : oldPassword, currentHash))
            throw new IllegalArgumentException("Current password is incorrect");

        String newHash = BCrypt.hashpw(newPassword, BCrypt.gensalt(12));
        try (Connection c = Db.get();
             PreparedStatement ps = c.prepareStatement("UPDATE users SET password_hash=? WHERE id=?")) {
            ps.setString(1, newHash);
            ps.setString(2, userId.trim());
            ps.executeUpdate();
        }
    }

    // == Ensure user exists (prevents FK failures in sessions/enrollments) ==
    public void ensureUserExists(String id, String name) throws Exception {
        if (id == null || id.isBlank()) return;
        try (Connection c = Db.get();
             PreparedStatement chk = c.prepareStatement("SELECT 1 FROM users WHERE id=?")) {
            chk.setString(1, id.trim());
            try (ResultSet rs = chk.executeQuery()) { if (rs.next()) return; }
        }
        String hash = BCrypt.hashpw("changeme", BCrypt.gensalt(10));
        try (Connection c = Db.get();
             PreparedStatement ins = c.prepareStatement(
                     "INSERT INTO users(id, name, password_hash, created_at) VALUES(?,?,?,?)")) {
            ins.setString(1, id.trim());
            ins.setString(2, (name == null || name.isBlank()) ? id.trim() : name.trim());
            ins.setString(3, hash);
            ins.setLong(4, System.currentTimeMillis());
            ins.executeUpdate();
        }
    }
}
