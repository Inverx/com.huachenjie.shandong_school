package caom.inverx.huachenjie;

import android.content.Context;
import java.lang.reflect.Method;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;

import java.io.File;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class FaceAutoHook {

    private static final String TAG = "[FaceAuto]";
    private static final String TARGET_PKG = "com.huachenjie.shandong_school";
    private static final String FACADE_A = "com.huachenjie.base.aliyun.detect_face.a";
    private static final String COMPANION =
            "com.huachenjie.base.aliyun.detect_face.DetectFaceFragment$Companion";
    private static final String COMPANION_LOCAL =
            "com.huachenjie.base.aliyun.detect_face.DetectFaceLocalCheckFragment$Companion";
    private static final String COMPANION_ONLINE =
            "com.huachenjie.base.aliyun.detect_face.DetectFaceCheckFragment$Companion";
    private static final String DETECT_FACE_FRAGMENT =
            "com.huachenjie.base.aliyun.detect_face.DetectFaceFragment";
    private static final String DETECT_FACE_LOCAL_FRAGMENT =
            "com.huachenjie.base.aliyun.detect_face.DetectFaceLocalCheckFragment";
    private static final String DETECT_FACE_ONLINE_FRAGMENT =
            "com.huachenjie.base.aliyun.detect_face.DetectFaceCheckFragment";
    private static final String USER_FACE_BEAN = "com.huachenjie.base.bean.UserFaceBean";
    private static final String DK2 = "com.zj.adlib.am2";
    private static final String DETECT_FACE_DELEGATE =
            "com.huachenjie.base.aliyun.detect_face.DetectFaceDelegate";
    private static final String FACE_TIP_DIALOG =
            "com.huachenjie.running.dialog.FaceRecognitionTipDialog";
    private static final String FACE_CAMERA_FRAGMENT =
            "com.huachenjie.base.aliyun.detect_face.FaceCameraFragment";
    private static final String DETECT_RESULT_BEAN =
            "com.huachenjie.base.aliyun.detect_face.DetectResultBean";
    private static final String TRACKING_INFO = "com.zj.adlib.pb9";
    private static final String RUN_FACE_DETECT_STATUS =
            "com.huachenjie.base.bean.RunFaceDetectStatus";
    private static final String UPLOAD_FILE_TYPE =
            "com.huachenjie.common.aliyun.file_upload.UploadFileType";

    private static final java.util.Random random = new java.util.Random();

    private static final int TIP_DELAY_MIN_MS = 1000;
    private static final int TIP_DELAY_MAX_MS = 5000;
    private static final int VERIFY_DELAY_MIN_MS = 1000;
    private static final int VERIFY_DELAY_MAX_MS = 4000;
    private static final long DEDUPE_WINDOW_MS = 15000L;

    private static final Map<String, Long> lastTrigger = new ConcurrentHashMap<>();
    private static final Map<String, Object> successSnapshots = new ConcurrentHashMap<>();
    private static final Map<Object, Boolean> confirmedDialogs =
            java.util.Collections.synchronizedMap(new java.util.WeakHashMap<Object, Boolean>());
    private static final AtomicBoolean triggerHooked = new AtomicBoolean(false);
    private static final AtomicBoolean dk2Hooked = new AtomicBoolean(false);
    private static final AtomicBoolean tipDialogHooked = new AtomicBoolean(false);
    private static final AtomicBoolean cameraSkipHooked = new AtomicBoolean(false);
    private static final AtomicBoolean proactiveSync = new AtomicBoolean(false);
    private static volatile Handler handler;
    private static volatile ClassLoader appClassLoader;

    static void setAppClassLoader(ClassLoader loader) {
        if (loader != null) {
            appClassLoader = loader;
        }
    }

    static void install(XC_LoadPackage.LoadPackageParam lpparam) {
        appClassLoader = lpparam.classLoader;
        ClassWatch.watch(FACADE_A, new ClassWatch.Callback() {
            @Override
            public void onClassAvailable(Class<?> cls) {
                hookFacade(cls);
            }
        });
        ClassWatch.watch(DETECT_FACE_FRAGMENT, new ClassWatch.Callback() {
            @Override
            public void onClassAvailable(Class<?> cls) {
                hookInitView(cls);
            }
        });
        ClassWatch.watch(DK2, new ClassWatch.Callback() {
            @Override
            public void onClassAvailable(Class<?> cls) {
                hookResultBroadcast(cls);
            }
        });
        ClassWatch.watch(FACE_TIP_DIALOG, new ClassWatch.Callback() {
            @Override
            public void onClassAvailable(Class<?> cls) {
                hookTipDialog(cls);
            }
        });
        ClassWatch.watch(FACE_CAMERA_FRAGMENT, new ClassWatch.Callback() {
            @Override
            public void onClassAvailable(Class<?> cls) {
                hookCameraSkip(cls);
            }
        });
        LateBinder.bind(lpparam, new LateBinder.Action() {
            @Override
            public boolean tryInstall(ClassLoader loader) {
                if (!triggerHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(FACADE_A, loader);
                    if (cls != null) {
                        hookFacade(cls);
                    }
                }
                if (!triggerHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(DETECT_FACE_FRAGMENT, loader);
                    if (cls != null) {
                        hookInitView(cls);
                    }
                }
                if (!triggerHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(DETECT_FACE_LOCAL_FRAGMENT, loader);
                    if (cls != null) {
                        hookInitView(cls);
                    }
                }
                if (!triggerHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(DETECT_FACE_ONLINE_FRAGMENT, loader);
                    if (cls != null) {
                        hookInitView(cls);
                    }
                }
                if (!triggerHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(COMPANION, loader);
                    if (cls != null) {
                        hookCompanion(cls);
                    }
                }
                if (!triggerHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(COMPANION_LOCAL, loader);
                    if (cls != null) {
                        hookCompanion(cls);
                    }
                }
                if (!triggerHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(COMPANION_ONLINE, loader);
                    if (cls != null) {
                        hookCompanion(cls);
                    }
                }
                if (!dk2Hooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(DK2, loader);
                    if (cls != null) {
                        hookResultBroadcast(cls);
                    }
                }
                if (!tipDialogHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(FACE_TIP_DIALOG, loader);
                    if (cls != null) {
                        hookTipDialog(cls);
                    }
                }
                if (!cameraSkipHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(FACE_CAMERA_FRAGMENT, loader);
                    if (cls != null) {
                        hookCameraSkip(cls);
                    }
                }
                boolean allDone = triggerHooked.get() && dk2Hooked.get()
                        && tipDialogHooked.get() && cameraSkipHooked.get();
                if (allDone && proactiveSync.compareAndSet(false, true)) {
                    HookLogger.logOnce("face-auto-sync-arm", TAG, "hooks 全部就绪：已安排主动同步缓存底脸");
                    getHandler().post(new Runnable() {
                        @Override
                        public void run() {
                            try {
                                File f = FaceCacheSync.syncIfNeeded();
                                if (f != null) {
                                    HookLogger.logOnce("face-auto-sync-done", TAG, "主动底图同步完成 " + f.getName());
                                }
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "主动底图同步异常: " + t);
                            }
                        }
                    });
                }
                return allDone;
            }
        });
    }

    private static boolean hookTipDialog(Class<?> dialogClass) {
        if (tipDialogHooked.get()) {
            return true;
        }
        try {
            XposedHelpers.findAndHookMethod(dialogClass, "initData",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            try {
                                autoConfirmTip(param.thisObject);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "提醒弹窗自动确认异常: " + t);
                            }
                        }
                    });

            XposedHelpers.findAndHookMethod(dialogClass, "initView",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            try {
                                autoConfirmTip(param.thisObject);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "initView 确认失败: " + t);
                            }
                        }
                    });
        } catch (Throwable t) {
            HookLogger.log(TAG, "提醒弹窗 hook 失败: " + t);
            return false;
        }
        if (tipDialogHooked.compareAndSet(false, true)) {
            HookLogger.logOnce("face-auto-tip-hook", TAG, "校验提醒弹窗已接管：将自动点击确认");
        }
        return true;
    }

    private static void autoConfirmTip(final Object dialog) {
        if (!ModuleConfig.isFaceEnabled() || !ModuleConfig.isFaceAutoEnabled()) {
            return;
        }
        if (confirmedDialogs.putIfAbsent(dialog, Boolean.TRUE) != null) {
            return;
        }
        long tipDelay = TIP_DELAY_MIN_MS + random.nextInt(TIP_DELAY_MAX_MS - TIP_DELAY_MIN_MS + 1);
        HookLogger.log(TAG, "检测到提醒弹窗，延时: " + tipDelay + " ms");
        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
            @Override
            public void run() {
                try {
                    Object cb = XposedHelpers.getObjectField(dialog, "callback");
                    if (cb == null) {
                        HookLogger.logOnce("face-auto-tip-null", TAG, "提醒弹窗 callback 为空，跳过自动点击");
                        return;
                    }
                    XposedHelpers.callMethod(cb, "invoke");
                    HookLogger.log(TAG, "触发提示弹窗确认，延时: " + tipDelay + " ms");
                    try {
                        XposedHelpers.callMethod(dialog, "dismissAllowingStateLoss");
                    } catch (Throwable ignored) {
                    }
                } catch (Throwable t) {
                    HookLogger.log(TAG, "确认弹窗执行失败: " + t);
                }
            }
        }, tipDelay);
    }

    private static boolean hookCameraSkip(Class<?> fragmentClass) {
        if (cameraSkipHooked.get()) {
            return true;
        }
        try {
            XposedHelpers.findAndHookMethod(fragmentClass, "startCamera",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (ModuleConfig.isFaceEnabled() && ModuleConfig.isFaceAutoEnabled()) {
                                    param.setResult(null);
                                    HookLogger.logOnce("face-auto-camera-skip", TAG,
                                            "face_auto 模式：已跳过人脸相机初始化（避免模拟器摄像头来源弹窗）");
                                }
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "相机跳过异常: " + t);
                            }
                        }
                    });
        } catch (Throwable t) {
            HookLogger.log(TAG, "startCamera 注入失败: " + t);
            return false;
        }
        if (cameraSkipHooked.compareAndSet(false, true)) {
            HookLogger.logOnce("face-auto-camera-hook", TAG, "已挂载相机启动监听");
        }
        return true;
    }

    private static boolean hookFacade(Class<?> facade) {
        if (triggerHooked.get()) {
            return true;
        }
        try {
            XposedHelpers.findAndHookMethod(facade, "a", USER_FACE_BEAN,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            try {
                                schedule(param.args[0]);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "门面触发调度异常: " + t);
                            }
                        }
                    });
        } catch (Throwable t) {
            HookLogger.log(TAG, "门面 hook 失败: " + t);
            return false;
        }
        if (triggerHooked.compareAndSet(false, true)) {
            HookLogger.logOnce("face-auto-trigger", TAG, "人脸校验门面触发器已接管 (a.a)");
        }
        return true;
    }

    private static boolean hookInitView(Class<?> fragmentClass) {
        if (triggerHooked.get()) {
            return true;
        }
        try {
            XposedHelpers.findAndHookMethod(fragmentClass, "initView",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            try {
                                Object bean = XposedHelpers.callMethod(param.thisObject, "getUserFaceBean");
                                schedule(bean);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "initView 触发异常: " + t);
                            }
                        }
                    });
        } catch (Throwable t) {
            HookLogger.log(TAG, "initView hook 失败: " + t);
            return false;
        }
        if (triggerHooked.compareAndSet(false, true)) {
            HookLogger.logOnce("face-auto-trigger", TAG,
                    "人脸校验 initView 触发器已接管 (" + fragmentClass.getSimpleName() + ")");
        }
        return true;
    }

    private static boolean hookCompanion(Class<?> companion) {
        if (triggerHooked.get()) {
            return true;
        }
        try {
            XposedHelpers.findAndHookMethod(companion, "a", USER_FACE_BEAN,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            try {
                                schedule(param.args[0]);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "Companion 触发调度异常: " + t);
                            }
                        }
                    });
        } catch (Throwable t) {
            HookLogger.log(TAG, "Companion hook 失败: " + t);
            return false;
        }
        if (triggerHooked.compareAndSet(false, true)) {
            HookLogger.logOnce("face-auto-trigger", TAG,
                    "人脸校验 Companion 触发器已接管 (" + companion.getSimpleName() + ")");
        }
        return true;
    }

    private static boolean hookResultBroadcast(Class<?> dk2) {
        if (dk2Hooked.get()) {
            return true;
        }
        try {

            Method targetMethod = null;
            for (Method m : dk2.getDeclaredMethods()) {
                if ("b".equals(m.getName()) && m.getParameterTypes().length == 2) {
                    targetMethod = m;
                    break;
                }
            }
            if (targetMethod == null) {
                HookLogger.log(TAG, "未在 " + dk2.getName() + " 中找到 2 参方法 b");
                return false;
            }
            XposedBridge.hookMethod(targetMethod, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    try {
                        intercept(param);
                    } catch (Throwable t) {
                        HookLogger.log(TAG, "结果拦截异常: " + t);
                    }
                }
            });
        } catch (Throwable t) {
            HookLogger.log(TAG, "结果注入挂载失败: " + t);
            return false;
        }
        if (dk2Hooked.compareAndSet(false, true)) {
            HookLogger.logOnce("face-auto-inject", TAG, "am2.b 结果注入点已接管 (反射直连)");
        }
        return true;
    }

    private static void intercept(XC_MethodHook.MethodHookParam param) {
        if (!ModuleConfig.isFaceEnabled() || !ModuleConfig.isFaceAutoEnabled()) {
            return;
        }
        Object bean = param.args[1];
        if (bean == null) {
            return;
        }
        boolean success = (Boolean) XposedHelpers.callMethod(bean, "getSuccess");
        String record = (String) XposedHelpers.callMethod(bean, "getRunRecordCode");
        if (record == null || record.length() == 0) {
            return;
        }
        String key = record + "#" + ((Integer) XposedHelpers.callMethod(bean, "getFaceCheckIndex"));
        if (success) {
            successSnapshots.put(key, bean);
            HookLogger.logOnce("face-auto-snapshot-" + key, TAG, "保存验证记录: " + key);
            return;
        }
        Object snapshot = successSnapshots.get(key);
        if (snapshot != null) {
            param.args[1] = snapshot;
            HookLogger.log(TAG, "失败结果已由成功快照替换 " + key);
        }
    }

    private static void schedule(final Object bean) {
        if (!ModuleConfig.isFaceEnabled() || !ModuleConfig.isFaceAutoEnabled() || bean == null) {
            return;
        }
        final String record = (String) XposedHelpers.callMethod(bean, "getRunRecordCode");
        if (record == null || record.length() == 0) {
            return;
        }
        final int index = (Integer) XposedHelpers.callMethod(bean, "getFaceCheckIndex");
        final String key = record + "#" + index;
        long now = System.currentTimeMillis();
        Long last = lastTrigger.get(key);
        if (last != null && now - last < DEDUPE_WINDOW_MS) {
            return;
        }
        lastTrigger.put(key, now);
        final ClassLoader loader = bean.getClass().getClassLoader();
        long verifyDelay = VERIFY_DELAY_MIN_MS + random.nextInt(VERIFY_DELAY_MAX_MS - VERIFY_DELAY_MIN_MS + 1);
        getHandler().postDelayed(new Runnable() {
            @Override
            public void run() {
                try {
                    runAutoUpload(loader, record, index, key);
                } catch (Throwable t) {
                    HookLogger.log(TAG, "自动核验上传失败: " + t);
                }
            }
        }, verifyDelay);
        HookLogger.log(TAG, "安排自动人脸核验: " + key + "，延时: " + verifyDelay + " ms");
    }

    private static void runAutoUpload(ClassLoader loader, String record, int index, String key) throws Exception {
        Class<?> tiClass = findClassSafe(TRACKING_INFO, loader);
        File photo = FaceHook.pickPhoto();
        if (photo == null && ModuleConfig.isFaceCacheEnabled()) {
            photo = FaceCacheSync.syncIfNeeded();
        }
        Object ti = FaceHook.buildTrackingInfo(tiClass, photo);
        if (ti == null) {
            HookLogger.logOnce("face-auto-no-photo", TAG, "底图库无可用照片，跳过自动校验，保持原始流程");
            return;
        }
        Class<?> uploadTypeClass = findClassSafe(UPLOAD_FILE_TYPE, loader);
        Object uploadType = Enum.valueOf((Class<? extends Enum>) uploadTypeClass, "UPLOAD_FACE_RUN");
        Class<?> statusClass = findClassSafe(RUN_FACE_DETECT_STATUS, loader);
        Object status = statusClass.newInstance();
        Class<?> delegateClass = findClassSafe(DETECT_FACE_DELEGATE, loader);
        Object delegate = delegateClass.newInstance();
        String filePath = "/data/data/" + TARGET_PKG + "/files/face_auto_" + System.currentTimeMillis() + ".jpg";
        XposedHelpers.callMethod(delegate, "x", Boolean.TRUE, Float.valueOf(100.0f), ti, filePath,
                Integer.valueOf(256), Integer.valueOf(256), uploadType, record, Integer.valueOf(index),
                status, Boolean.TRUE);
        HookLogger.logOnce("face-auto-uploaded-" + key, TAG, "触发自动人脸核验: " + key);
        getHandler().postDelayed(new Runnable() {
            @Override
            public void run() {
                try {
                    File f = new File(filePath);
                    if (f.exists()) f.delete();
                } catch (Throwable ignored) {}
            }
        }, 10000L);
    }

    private static Class<?> findClassSafe(String name, ClassLoader loader) throws ClassNotFoundException {
        try {
            return Class.forName(name, false, loader);
        } catch (Throwable t) {
            try {
                if (appClassLoader != null) {
                    return Class.forName(name, false, appClassLoader);
                }
            } catch (Throwable ignored) {
            }
            Class<?> cls = XposedHelpers.findClassIfExists(name, loader);
            if (cls != null) {
                return cls;
            }
            throw new ClassNotFoundException("无法从指定 loader 解析类: " + name);
        }
    }

    private static Handler getHandler() {
        if (handler == null) {
            synchronized (FaceAutoHook.class) {
                if (handler == null) {
                    HandlerThread thread = new HandlerThread("FaceAutoThread");
                    thread.start();
                    handler = new Handler(thread.getLooper());
                }
            }
        }
        return handler;
    }
}
