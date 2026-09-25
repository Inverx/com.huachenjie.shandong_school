package caom.inverx.huachenjie;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import de.robv.android.xposed.XposedBridge;

final class HookLogger {

    private static final String TARGET_PKG = "com.huachenjie.shandong_school";
    private static final File LOG_FILE = new File("/data/data/" + TARGET_PKG + "/files/hook_runtime.log");
    private static final long MAX_LOG_SIZE = 256L * 1024L;
    private static final Object LOCK = new Object();
    private static final Map<String, Boolean> ONCE = new ConcurrentHashMap<>();

    private HookLogger() {
    }

    static void log(String tag, String message) {
        String line = format(tag, message);
        XposedBridge.log(line);
        synchronized (LOCK) {
            try {
                File parent = LOG_FILE.getParentFile();
                if (parent != null && !parent.exists()) {

                    parent.mkdirs();
                }
                if (LOG_FILE.exists() && LOG_FILE.length() > MAX_LOG_SIZE) {
                    trimToTail();
                }
                try (FileOutputStream fos = new FileOutputStream(LOG_FILE, true)) {
                    fos.write(line.getBytes(StandardCharsets.UTF_8));
                    fos.write('\n');
                }
            } catch (Throwable ignored) {
            }
        }
    }

    static void logOnce(String key, String tag, String message) {
        if (ONCE.putIfAbsent(key, Boolean.TRUE) == null) {
            log(tag, message);
        }
    }

    static String logFilePath() {
        return LOG_FILE.getAbsolutePath();
    }

    private static String format(String tag, String message) {
        synchronized (LOCK) {
            long now = System.currentTimeMillis();
            StringBuilder sb = new StringBuilder();
            sb.append('[');
            appendTime(sb, now);
            sb.append(']').append(tag).append(' ').append(message);
            return sb.toString();
        }
    }

    private static void appendTime(StringBuilder sb, long millis) {
        long totalSec = millis / 1000L;
        int ms = (int) (millis % 1000L);
        int hour = (int) ((totalSec / 3600L) % 24L);
        int minute = (int) ((totalSec / 60L) % 60L);
        int second = (int) (totalSec % 60L);
        append2(sb, hour);
        sb.append(':');
        append2(sb, minute);
        sb.append(':');
        append2(sb, second);
        sb.append('.');
        append3(sb, ms);
    }

    private static void append2(StringBuilder sb, int v) {
        if (v < 10) {
            sb.append('0');
        }
        sb.append(v);
    }

    private static void append3(StringBuilder sb, int v) {
        if (v < 100) {
            sb.append('0');
        }
        if (v < 10) {
            sb.append('0');
        }
        sb.append(v);
    }

    private static void trimToTail() {
        try {
            byte[] all;
            try (FileInputStream fis = new FileInputStream(LOG_FILE)) {
                all = readAll(fis);
            }
            int keepFrom = Math.max(0, all.length - (int) (MAX_LOG_SIZE / 2));
            try (FileOutputStream fos = new FileOutputStream(LOG_FILE, false)) {
                fos.write(all, keepFrom, all.length - keepFrom);
            }
        } catch (IOException ignored) {
        }
    }

    private static byte[] readAll(FileInputStream fis) throws IOException {
        byte[] buf = new byte[8192];
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
        int n;
        while ((n = fis.read(buf)) > 0) {
            bos.write(buf, 0, n);
        }
        return bos.toByteArray();
    }
}
