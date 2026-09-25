package caom.inverx.huachenjie;

import java.io.File;
import java.io.FileInputStream;
import java.util.Properties;

final class ModuleConfig {

    private static final String TARGET_PKG = "com.huachenjie.shandong_school";
    private static final File CONFIG_FILE = new File("/data/data/" + TARGET_PKG + "/files/hook_config.properties");

    private static final Object LOCK = new Object();
    private static volatile long lastLoaded = Long.MIN_VALUE;
    private static volatile boolean wifiEnabled = true;
    private static volatile boolean locationEnabled = true;
    private static volatile boolean faceEnabled = true;
    private static volatile boolean faceCacheEnabled = true;
    private static volatile boolean faceAutoEnabled = true;

    private ModuleConfig() {
    }

    static boolean isWifiEnabled() {
        reloadIfNeeded();
        return wifiEnabled;
    }

    static boolean isLocationEnabled() {
        reloadIfNeeded();
        return locationEnabled;
    }

    static boolean isFaceEnabled() {
        reloadIfNeeded();
        return faceEnabled;
    }

    static boolean isFaceCacheEnabled() {
        reloadIfNeeded();
        return faceCacheEnabled;
    }

    static boolean isFaceAutoEnabled() {
        reloadIfNeeded();
        return faceAutoEnabled;
    }

    private static void reloadIfNeeded() {
        long modified = CONFIG_FILE.exists() ? CONFIG_FILE.lastModified() : Long.MIN_VALUE;
        if (modified == lastLoaded) {
            return;
        }
        synchronized (LOCK) {
            modified = CONFIG_FILE.exists() ? CONFIG_FILE.lastModified() : Long.MIN_VALUE;
            if (modified == lastLoaded) {
                return;
            }
            if (!CONFIG_FILE.exists()) {
                wifiEnabled = true;
                locationEnabled = true;
                faceEnabled = true;
                faceCacheEnabled = true;
                faceAutoEnabled = true;
                lastLoaded = Long.MIN_VALUE;
                return;
            }
            Properties props = new Properties();
            try (FileInputStream fis = new FileInputStream(CONFIG_FILE)) {
                props.load(fis);
                wifiEnabled = getBoolean(props, "wifi", true);
                locationEnabled = getBoolean(props, "location", true);
                faceEnabled = getBoolean(props, "face", true);
                faceCacheEnabled = getBoolean(props, "face_cache", true);
                faceAutoEnabled = getBoolean(props, "face_auto", true);
                lastLoaded = modified;
                HookLogger.logOnce("config-ok", "[Config]", "配置已载入: wifi=" + wifiEnabled
                        + " location=" + locationEnabled + " face=" + faceEnabled
                        + " face_cache=" + faceCacheEnabled + " face_auto=" + faceAutoEnabled);
            } catch (Throwable t) {
                wifiEnabled = true;
                locationEnabled = true;
                faceEnabled = true;
                faceCacheEnabled = true;
                faceAutoEnabled = true;
                lastLoaded = Long.MIN_VALUE;
                HookLogger.log("[Config]", "读取配置失败，使用默认配置: " + t);
            }
        }
    }

    private static boolean getBoolean(Properties props, String key, boolean def) {
        String value = props.getProperty(key);
        if (value == null) {
            return def;
        }
        value = value.trim();
        if (value.length() == 0) {
            return def;
        }
        return "1".equals(value) || "true".equalsIgnoreCase(value) || "yes".equalsIgnoreCase(value) || "on".equalsIgnoreCase(value);
    }
}
