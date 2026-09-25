package caom.inverx.huachenjie;

import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.CheckBox;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Space;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashSet;
import java.util.Set;
import java.util.Properties;

public class MainActivity extends AppCompatActivity {

    private static final String PREFS = "face_prefs";
    private static final String KEY_URIS = "face_uris";
    private static final String KEY_WIFI = "enable_wifi";
    private static final String KEY_LOCATION = "enable_location";
    private static final String KEY_FACE = "enable_face";
    private static final String TARGET_PKG = "com.huachenjie.shandong_school";
    private static final String TARGET_FACE_DIR = "/data/data/" + TARGET_PKG + "/files/face";
    private static final String TARGET_CONFIG_FILE = "/data/data/" + TARGET_PKG + "/files/hook_config.properties";

    private TextView statusText;
    private SharedPreferences prefs;
    private ActivityResultLauncher<String[]> pickLauncher;
    private CheckBox wifiBox;
    private CheckBox locationBox;
    private CheckBox faceBox;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);

        pickLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenMultipleDocuments(), uris -> {
                    if (uris == null || uris.isEmpty()) {
                        return;
                    }
                    Set<String> saved = new HashSet<>();
                    for (Uri uri : uris) {
                        try {
                            getContentResolver().takePersistableUriPermission(
                                    uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
                            saved.add(uri.toString());
                        } catch (Throwable t) {
                            saved.add(uri.toString());
                        }
                    }
                    prefs.edit().putStringSet(KEY_URIS, saved).apply();
                    refreshStatus();
                });

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(16);
        root.setPadding(pad, pad, pad, pad);
        scroll.addView(root);

        TextView title = new TextView(this);
        title.setText("Hook闪动");
        title.setTextSize(19);
        title.setPadding(0, 0, 0, dp(12));
        root.addView(title);

        wifiBox = new CheckBox(this);
        wifiBox.setText("启用 WiFi 状态伪装");
        wifiBox.setChecked(prefs.getBoolean(KEY_WIFI, true));
        root.addView(wifiBox);

        locationBox = new CheckBox(this);
        locationBox.setText("启用虚拟定位检测规避");
        locationBox.setChecked(prefs.getBoolean(KEY_LOCATION, true));
        root.addView(locationBox);

        faceBox = new CheckBox(this);
        faceBox.setText("启用人脸底图替换");
        faceBox.setChecked(prefs.getBoolean(KEY_FACE, true));
        root.addView(faceBox);

        Space gap0 = new Space(this);
        gap0.setMinimumHeight(dp(12));
        root.addView(gap0);

        Button pickBtn = new Button(this);
        pickBtn.setText("选择照片");
        pickBtn.setOnClickListener(v -> pickLauncher.launch(new String[]{"image/*"}));
        root.addView(pickBtn);

        Space gap1 = new Space(this);
        gap1.setMinimumHeight(dp(6));
        root.addView(gap1);

        Button syncBtn = new Button(this);
        syncBtn.setText("保存并同步配置");
        syncBtn.setOnClickListener(v -> syncToTarget());
        root.addView(syncBtn);

        Space gap2 = new Space(this);
        gap2.setMinimumHeight(dp(6));
        root.addView(gap2);

        Button clearBtn = new Button(this);
        clearBtn.setText("清空选择");
        clearBtn.setOnClickListener(v -> {
            prefs.edit().remove(KEY_URIS).apply();
            refreshStatus();
        });
        root.addView(clearBtn);

        Button logBtn = new Button(this);
        logBtn.setText("查看日志路径");
        logBtn.setOnClickListener(v -> {
            statusText.setText("日志路径：" + HookLogger.logFilePath());
        });
        root.addView(logBtn);

        statusText = new TextView(this);
        statusText.setTextSize(12);
        statusText.setPadding(0, dp(12), 0, 0);
        root.addView(statusText);

        TextView contactText = new TextView(this);
        contactText.setText("作者联系github：GitHub.com/inverx，telegram通知群道t.me/Inverx200，讨论群t.me/Inverx501");
        contactText.setTextSize(11);
        contactText.setPadding(0, dp(16), 0, dp(12));
        root.addView(contactText);

        ensureFaceDirectoriesPreCreated();

        setContentView(scroll);
        refreshStatus();
    }

    private void refreshStatus() {
        Set<String> uris = prefs.getStringSet(KEY_URIS, null);
        int count = uris == null ? 0 : uris.size();
        statusText.setText("已选照片数量: " + count + "\n"
                + "底图库路径: " + TARGET_FACE_DIR + "\n"
                + "运行日志: " + HookLogger.logFilePath());
    }

    private void syncToTarget() {
        saveSwitches();
        Set<String> uris = prefs.getStringSet(KEY_URIS, null);
        statusText.setText("正在同步配置");
        new Thread(() -> {
            try {
                File syncDir = new File(getFilesDir(), "face_sync");
                if (syncDir.exists()) {
                    File[] olds = syncDir.listFiles();
                    if (olds != null) {
                        for (File f : olds) {
                            f.delete();
                        }
                    }
                }
                syncDir.mkdirs();
                File photoDir = new File(syncDir, "photos");
                if (photoDir.exists()) {
                    File[] olds = photoDir.listFiles();
                    if (olds != null) {
                        for (File f : olds) {
                            f.delete();
                        }
                    }
                }
                photoDir.mkdirs();
                int index = 0;
                int photoCount = 0;
                if (uris != null) {
                    for (String s : uris) {
                        Uri uri = Uri.parse(s);
                        File out = new File(photoDir, "img_" + (index++) + ".jpg");
                        try (InputStream in = getContentResolver().openInputStream(uri);
                             FileOutputStream fos = new FileOutputStream(out)) {
                            if (in == null) {
                                continue;
                            }
                            byte[] buf = new byte[8192];
                            int n;
                            while ((n = in.read(buf)) > 0) {
                                fos.write(buf, 0, n);
                            }
                            photoCount++;
                        } catch (Throwable ignored) {
                            out.delete();
                        }
                    }
                }
                File configFile = new File(syncDir, "hook_config.properties");
                writeConfigFile(configFile);

                StringBuilder cmd = new StringBuilder();
                cmd.append("mkdir -p ").append(TARGET_FACE_DIR)
                        .append(" && mkdir -p /data/data/").append(TARGET_PKG).append("/files");
                if (photoCount > 0) {
                    cmd.append(" && rm -f ").append(TARGET_FACE_DIR).append("/*")
                            .append(" && cp -f ").append(photoDir.getAbsolutePath()).append("/* ")
                            .append(TARGET_FACE_DIR).append("/");
                }
                cmd.append(" && cp -f ").append(configFile.getAbsolutePath()).append(" ")
                        .append(TARGET_CONFIG_FILE);
                String result = runAsRoot(cmd.toString());
                final int syncedPhotos = photoCount;
                runOnUiThread(() -> statusText.setText(
                        result + (syncedPhotos > 0 ? "\n本次同步照片 " + syncedPhotos + " 张" : "\n本次未同步照片，仅更新开关配置。")));
            } catch (Throwable t) {
                runOnUiThread(() -> statusText.setText("同步失败: " + t));
            }
        }).start();
    }

    private String runAsRoot(String cmd) {
        String[] suCandidates = {"su", "/system/bin/su", "/system/xbin/su", "/sbin/su"};
        for (String su : suCandidates) {
            try {
                Process p = new ProcessBuilder(su, "-c", cmd).redirectErrorStream(true).start();
                java.util.Scanner s = new java.util.Scanner(p.getInputStream()).useDelimiter("\\A");
                String out = s.hasNext() ? s.next() : "";
                int code = p.waitFor();
                if (code == 0) {
                    return "同步成功\n底图库目录：" + TARGET_FACE_DIR + "\n" + out;
                }
                return "su 执行失败, code=" + code + ")\n" + out;
            } catch (Throwable ignored) {
            }
        }
        return "未检测到 su 工具";
    }

    private void saveSwitches() {
        prefs.edit()
                .putBoolean(KEY_WIFI, wifiBox.isChecked())
                .putBoolean(KEY_LOCATION, locationBox.isChecked())
                .putBoolean(KEY_FACE, faceBox.isChecked())
                .apply();
    }

    private void writeConfigFile(File configFile) throws Exception {
        Properties props = new Properties();
        props.setProperty("wifi", String.valueOf(wifiBox.isChecked()));
        props.setProperty("location", String.valueOf(locationBox.isChecked()));
        props.setProperty("face", String.valueOf(faceBox.isChecked()));
        try (OutputStream out = new FileOutputStream(configFile)) {
            props.store(out, null);
        }
    }

    private void ensureFaceDirectoriesPreCreated() {
        new Thread(() -> {
            try {
                File pubDir = new File("/sdcard/闪动校园/face/default");
                if (!pubDir.exists()) {
                    pubDir.mkdirs();
                }
                File extDir = new File("/sdcard/Android/data/" + TARGET_PKG + "/files/face/default");
                if (!extDir.exists()) {
                    extDir.mkdirs();
                }
                runAsRoot("mkdir -p " + TARGET_FACE_DIR + "/default && mkdir -p /data/data/" + TARGET_PKG + "/files");
            } catch (Throwable ignored) {
            }
        }).start();
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
