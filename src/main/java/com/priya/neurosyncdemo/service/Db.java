package com.priya.neurosyncdemo.service;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

import java.sql.Connection;
import java.sql.Statement;
import java.util.Optional;

public final class Db {
    private static final HikariDataSource DS;

    static {
        HikariConfig cfg = new HikariConfig();

        String url  = Optional.ofNullable(System.getenv("NS_DB_URL"))
                .orElse("jdbc:mysql://localhost:3306/neurosync?useSSL=false&serverTimezone=UTC&allowPublicKeyRetrieval=true");
        String user = Optional.ofNullable(System.getenv("NS_DB_USER")).orElse("neuro");
        String pass = Optional.ofNullable(System.getenv("NS_DB_PASS")).orElse("neuro_pass_123");

        cfg.setJdbcUrl(url);
        cfg.setUsername(user);
        cfg.setPassword(pass);
        cfg.setMaximumPoolSize(8);
        cfg.setMinimumIdle(1);
        cfg.setDriverClassName("com.mysql.cj.jdbc.Driver");

        DS = new HikariDataSource(cfg);

        try (Connection c = DS.getConnection(); Statement s = c.createStatement()) {

            // --- SINGLE definitive users table ---
            s.execute("""
              CREATE TABLE IF NOT EXISTS users(
                id            VARCHAR(64) PRIMARY KEY,     -- student id / roll no
                name          VARCHAR(255) NOT NULL,
                email         VARCHAR(255) UNIQUE,
                password_hash VARCHAR(72)  NOT NULL,
                created_at    BIGINT       NOT NULL
              )
            """);

            // courses + enrollments
            s.execute("""
              CREATE TABLE IF NOT EXISTS courses(
                id    VARCHAR(64) PRIMARY KEY,
                title VARCHAR(255) NOT NULL
              )
            """);

            s.execute("""
              CREATE TABLE IF NOT EXISTS enrollments(
                user_id   VARCHAR(64) NOT NULL,
                course_id VARCHAR(64) NOT NULL,
                PRIMARY KEY(user_id, course_id),
                FOREIGN KEY(user_id)   REFERENCES users(id)   ON DELETE CASCADE,
                FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
              )
            """);

            // learning sessions (per user x course)
            s.execute("""
              CREATE TABLE IF NOT EXISTS sessions(
                id         BIGINT PRIMARY KEY AUTO_INCREMENT,
                student_id VARCHAR(64) NOT NULL,
                course_id  VARCHAR(64),
                started_at BIGINT NOT NULL,
                FOREIGN KEY(student_id) REFERENCES users(id)   ON DELETE CASCADE,
                FOREIGN KEY(course_id)  REFERENCES courses(id) ON DELETE SET NULL
              )
            """);

            // emotion events
            s.execute("""
              CREATE TABLE IF NOT EXISTS emotion_events(
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                session_id BIGINT NOT NULL,
                ts BIGINT NOT NULL,
                source VARCHAR(32),
                top_emotion VARCHAR(32),
                derived_emotion VARCHAR(32),
                confidence DOUBLE,
                happy DOUBLE, sad DOUBLE, angry DOUBLE, calm DOUBLE,
                confused DOUBLE, surprised DOUBLE, disgusted DOUBLE, fear DOUBLE,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
              )
            """);

            // points
            s.execute("""
              CREATE TABLE IF NOT EXISTS points_ledger(
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id VARCHAR(64) NOT NULL,
                delta   INT NOT NULL,
                reason  VARCHAR(255),
                ts      BIGINT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
              )
            """);

        } catch (Exception e) {
            throw new RuntimeException("DB bootstrap failed: " + e.getMessage(), e);
        }
    }

    private Db() {}
    public static Connection get() throws Exception { return DS.getConnection(); }
}
