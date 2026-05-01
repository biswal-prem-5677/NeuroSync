package com.priya.neurosyncdemo.util;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

    public class LoggerUtil {
        private static final Path LOG = Path.of("session_log.txt");
        public static void log(String line) {
            try {
                Files.writeString(LOG, line + System.lineSeparator(),
                        StandardOpenOption.CREATE, StandardOpenOption.APPEND);
            } catch (Exception ignored) {}
        }
    }


