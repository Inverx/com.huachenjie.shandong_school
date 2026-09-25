package caom.inverx.huachenjie;

import java.io.File;
import java.lang.reflect.Method;
import android.content.Context;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

final class FaceCacheSync {

    private static final String TAG = "[FaceSync]";
    private static final String TARGET_PKG = "com.huachenjie.shandong_school";
    private static final long MIN_SIZE = 10 * 1024L;
    private static final long RESCAN_INTERVAL_MS = 15 * 1000L;
    private static final long FAIL_RETRY_MS = 2 * 1000L;
    private static volatile long lastScan = 0L;
    private static volatile long lastOkScan = 0L;

    private static final File OUT_DIR =
            new File("/data/data/" + TARGET_PKG + "/files/face/default");
    private static final File OUT_FILE = new File(OUT_DIR, "registered_auto.jpg");

    static {
        try {
            if (!OUT_DIR.exists()) {
                OUT_DIR.mkdirs();
            }
        } catch (Throwable ignored) {
        }
    }

    static boolean saveAsRegisteredAuto(File src) {
        if (!ModuleConfig.isFaceCacheEnabled()) {
            return false;
        }
        if (src == null || !src.exists() || src.length() < MIN_SIZE) {
            return false;
        }
        try {
            if (!OUT_DIR.exists() && !OUT_DIR.mkdirs()) {
                HookLogger.log(TAG, "创建目录失败: " + OUT_DIR);
                return false;
            }
            if (!OUT_FILE.exists() || OUT_FILE.length() != src.length()) {
                copy(src, OUT_FILE);
            }
            lastOkScan = System.currentTimeMillis();
            HookLogger.logOnce("face-sync-direct", TAG, "直连底脸已同步: " + src.getName()
                    + " (" + src.length() + "B) -> " + OUT_FILE.getAbsolutePath());
            return true;
        } catch (Throwable t) {
            HookLogger.log(TAG, "直连底脸保存失败: " + t);
            return false;
        }
    }

    static File syncIfNeeded() {
        if (!ModuleConfig.isFaceCacheEnabled()) {
            return null;
        }
        long now = System.currentTimeMillis();
        if (now - lastOkScan < RESCAN_INTERVAL_MS) {
            if (OUT_FILE.exists() && OUT_FILE.length() >= MIN_SIZE) {
                return OUT_FILE;
            }
            return null;
        }
        if (now - lastScan < FAIL_RETRY_MS) {
            return null;
        }
        lastScan = now;
        try {
            if (!OUT_DIR.exists()) {
                OUT_DIR.mkdirs();
            }
            if (OUT_FILE.exists() && OUT_FILE.length() >= MIN_SIZE) {
                lastOkScan = now;
                return OUT_FILE;
            }
            List<File> candidates = new ArrayList<>();

            try {
                Class<?> utilsCls = Class.forName("com.blankj.utilcode.util.Utils");
                Method getApp = utilsCls.getMethod("getApp");
                Object app = getApp.invoke(null);
                if (app instanceof Context) {
                    File extCache = ((Context) app).getExternalCacheDir();
                    if (extCache != null) {
                        collectAll(new File(extCache, "FaceRecognitionCache"), candidates);
                    }
                }
            } catch (Throwable ignored) {
            }

            collectAll(new File("/sdcard/Android/data/" + TARGET_PKG + "/cache/FaceRecognitionCache"), candidates);

            if (candidates.isEmpty()) {
                collectAll(new File("/data/data/" + TARGET_PKG + "/cache/FaceRecognitionCache"), candidates);
            }

            if (candidates.isEmpty()) {
                collectAll(new File("/storage/emulated/0/Android/data/" + TARGET_PKG + "/cache/FaceRecognitionCache"), candidates);
            }
            if (candidates.isEmpty()) {
                collectJpgShallow(new File("/sdcard/Android/data/" + TARGET_PKG + "/cache"), candidates);
                collectJpgShallow(new File("/data/data/" + TARGET_PKG + "/cache"), candidates);
                collectJpgShallow(new File("/data/data/" + TARGET_PKG + "/cache/thumb"), candidates);
                collectJpgShallow(new File("/data/data/" + TARGET_PKG + "/cache/image"), candidates);
            }
            if (candidates.isEmpty()) {
                HookLogger.log(TAG, "未找到缓存底脸候选文件（已扫描 external/internal FaceRecognitionCache 及 cache 子目录）");
                return null;
            }
            Collections.sort(candidates, new Comparator<File>() {
                @Override
                public int compare(File a, File b) {
                    return Long.compare(b.length(), a.length());
                }
            });
            File best = candidates.get(0);
            if (!OUT_DIR.exists() && !OUT_DIR.mkdirs()) {
                HookLogger.log(TAG, "创建目录失败: " + OUT_DIR);
                return null;
            }
            if (!OUT_FILE.exists() || OUT_FILE.length() != best.length()) {
                copy(best, OUT_FILE);
            }
            lastOkScan = now;
            HookLogger.logOnce("face-sync-hit", TAG, "缓存底脸已同步: " + best.getName()
                    + " (" + best.length() + "B) -> " + OUT_FILE.getAbsolutePath());
            return OUT_FILE;
        } catch (Throwable t) {
            HookLogger.log(TAG, "缓存底脸同步失败: " + t);
            return null;
        }
    }

    private static void collectAll(File dir, List<File> out) {
        File[] files = dir.listFiles();
        if (files == null) {
            HookLogger.log(TAG, "目录不可访问: " + dir.getAbsolutePath());
            return;
        }
        HookLogger.log(TAG, "扫描目录: " + dir.getAbsolutePath() + " (" + files.length + "  个文件");
        for (File f : files) {
            if (f.isFile() && f.length() >= MIN_SIZE && isImage(f)) {
                out.add(f);
            }
        }
        if (out.isEmpty()) {

            int logged = 0;
            for (File f : files) {
                if (f.isFile() && f.length() >= MIN_SIZE && logged < 3) {
                    HookLogger.log(TAG, "候选未通过格式检测: " + f.getName()
                            + " (" + f.length() + "B, magic=" + readMagicHex(f) + ")");
                    logged++;
                }
            }
        }
    }

    private static void collectJpgShallow(File dir, List<File> out) {
        File[] files = dir.listFiles();
        if (files == null) {
            return;
        }
        for (File f : files) {

            if (f.isFile() && f.length() >= MIN_SIZE && isImage(f)) {
                out.add(f);
            }
        }
    }

    private static boolean isImage(File f) {
        try (InputStream in = new FileInputStream(f)) {
            byte[] head = new byte[4];
            int n = in.read(head);
            if (n < 3) {
                return false;
            }

            if ((head[0] & 0xFF) == 0xFF && (head[1] & 0xFF) == 0xD8 && (head[2] & 0xFF) == 0xFF) {
                return true;
            }

            if (n >= 4 && (head[0] & 0xFF) == 0x89 && (head[1] & 0xFF) == 0x50
                    && (head[2] & 0xFF) == 0x4E && (head[3] & 0xFF) == 0x47) {
                return true;
            }

            if (n >= 4 && (head[0] & 0xFF) == 0x52 && (head[1] & 0xFF) == 0x49
                    && (head[2] & 0xFF) == 0x46 && (head[3] & 0xFF) == 0x46) {
                return true;
            }

            if ((head[0] & 0xFF) == 0x42 && (head[1] & 0xFF) == 0x4D) {
                return true;
            }
            return false;
        } catch (Throwable t) {
            return false;
        }
    }

    private static String readMagicHex(File f) {
        try (InputStream in = new FileInputStream(f)) {
            byte[] head = new byte[4];
            int n = in.read(head);
            if (n <= 0) {
                return "empty";
            }
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < n; i++) {
                if (i > 0) sb.append(' ');
                sb.append(String.format("%02X", head[i] & 0xFF));
            }
            return sb.toString();
        } catch (Throwable t) {
            return "err:" + t.getClass().getSimpleName();
        }
    }

    private static void copy(File src, File dst) throws Exception {
        try (InputStream in = new FileInputStream(src);
             OutputStream out = new FileOutputStream(dst, false)) {
            byte[] buf = new byte[65536];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
        }
    }
}
