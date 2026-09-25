package caom.inverx.huachenjie;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

import java.io.File;
import java.lang.reflect.Constructor;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.WeakHashMap;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class FaceHook {

    private static final String TAG = "[FaceHook]";
    private static final String TARGET_PKG = "com.huachenjie.shandong_school";
    private static final String FACE_TOOL = "com.huachenjie.base.aliyun.detect_face.analyzer.FaceTool";
    private static final String USER_FACE_BEAN = "com.huachenjie.base.bean.UserFaceBean";

    private static volatile ClassLoader appClassLoader;

    static void setAppClassLoader(ClassLoader loader) {
        if (loader != null) {
            appClassLoader = loader;
        }
    }
    private static final Random random = new Random();
    private static final Map<Object, Object> injectedCache =
            Collections.synchronizedMap(new WeakHashMap<Object, Object>());
    private static final Map<Class<?>, Constructor<?>> tiCtorCache =
            Collections.synchronizedMap(new WeakHashMap<Class<?>, Constructor<?>>());
    private static volatile boolean folderLogged = false;
    private static volatile boolean facePhotoAvailable = false;
    private static volatile Object zeroFrame;

    static void install(XC_LoadPackage.LoadPackageParam lpparam) {
        appClassLoader = lpparam.classLoader;
        HookLogger.logOnce("face-install", TAG, "注册人脸核验底图注入（等待应用类可用）");

        ClassWatch.watch(FACE_TOOL, new ClassWatch.Callback() {
            @Override
            public void onClassAvailable(Class<?> cls) {
                hookFaceTool(cls);
            }
        });
        ClassWatch.watch(USER_FACE_BEAN, new ClassWatch.Callback() {
            @Override
            public void onClassAvailable(Class<?> cls) {
                hookUserFaceBean(cls);
            }
        });
        LateBinder.bind(lpparam, new LateBinder.Action() {
            private boolean faceToolDone;
            private boolean userFaceBeanDone;

            @Override
            public boolean tryInstall(ClassLoader loader) {
                if (!faceToolDone) {
                    Class<?> cls = XposedHelpers.findClassIfExists(FACE_TOOL, loader);
                    if (cls != null) {
                        hookFaceTool(cls);
                        faceToolDone = true;
                    }
                }
                if (!userFaceBeanDone) {
                    Class<?> cls = XposedHelpers.findClassIfExists(USER_FACE_BEAN, loader);
                    if (cls != null) {
                        hookUserFaceBean(cls);
                        userFaceBeanDone = true;
                    }
                }
                return faceToolDone && userFaceBeanDone;
            }
        });
    }

    private static final java.util.concurrent.atomic.AtomicBoolean faceToolHooked =
            new java.util.concurrent.atomic.AtomicBoolean(false);
    private static final java.util.concurrent.atomic.AtomicBoolean userFaceBeanHooked =
            new java.util.concurrent.atomic.AtomicBoolean(false);

    private static void hookFaceTool(Class<?> faceTool) {
        if (!faceToolHooked.compareAndSet(false, true)) {
            return;
        }
        HookLogger.logOnce("face-ftool-hook", TAG, "FaceTool 就绪，挂载帧注入");
        try {
            XposedHelpers.findAndHookMethod(faceTool, "f",
                    "androidx.camera.core.ImageProxy",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isFaceEnabled()) {
                                    facePhotoAvailable = false;
                                    injectedCache.clear();
                                    zeroFrame = null;
                                    return;
                                }
                                if (ModuleConfig.isFaceAutoEnabled()) {
                                    Object zf = zeroFrame;
                                    if (zf != null) {
                                        param.setResult(zf);
                                    }
                                    return;
                                }
                                Object cached = injectedCache.get(param.thisObject);
                                if (cached != null) {
                                    param.setResult(cached);
                                }
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "f 回调失败: " + t);
                            }
                        }

                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isFaceEnabled()) {
                                    return;
                                }
                                Object original = param.getResult();
                                if (original == null) {
                                    return;
                                }
                                if (ModuleConfig.isFaceAutoEnabled()) {
                                    if (zeroFrame == null) {
                                        zeroFrame = buildZeroFrame(original);
                                        HookLogger.logOnce("face-auto-zero-frame", TAG,
                                                "face_auto 开启：分析器路径让位于自动上传流程");
                                    }
                                    param.setResult(zeroFrame);
                                    return;
                                }
                                if (injectedCache.containsKey(param.thisObject)) {
                                    return;
                                }
                                Object injected = buildTrackingInfo(original);
                                if (injected != null) {
                                    injectedCache.put(param.thisObject, injected);
                                    param.setResult(injected);
                                } else {
                                    facePhotoAvailable = false;
                                    injectedCache.remove(param.thisObject);
                                }
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "帧处理失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("face-ftool-f", TAG, "FaceTool.f 帧注入完成");
        } catch (Throwable t) {
            HookLogger.log(TAG, "FaceTool.f 注入失败: " + t);
        }

        try {
            XposedHelpers.findAndHookMethod(faceTool, "c",
                    "com.insightface.sdk.inspireface.base.FaceFeature",
                    "com.insightface.sdk.inspireface.base.FaceFeature",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isFaceEnabled()) {
                                    return;
                                }

                                param.setResult(1.0f);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "c 回调失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("face-compare", TAG, "FaceTool.c 相似度置为 1.0");
        } catch (Throwable t) {
            HookLogger.log(TAG, "FaceTool.c 注入失败: " + t);
        }

        try {
            Class<?> companionClass = null;
            try {
                Object instanceObj = XposedHelpers.getStaticObjectField(faceTool, "a");
                if (instanceObj != null) {
                    companionClass = instanceObj.getClass();
                }
            } catch (Throwable ignored) {
            }
            if (companionClass == null) {
                companionClass = XposedHelpers.findClassIfExists(
                        "com.huachenjie.base.aliyun.detect_face.analyzer.FaceTool$a", faceTool.getClassLoader());
            }
            if (companionClass != null) {
                XposedHelpers.findAndHookMethod(companionClass, "b", String.class, new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) {
                        try {
                            File f = (File) param.getResult();
                            if (f != null && f.exists()) {
                                FaceCacheSync.saveAsRegisteredAuto(f);
                            }
                        } catch (Throwable t) {
                            HookLogger.log(TAG, "底脸缓存捕获异常: " + t);
                        }
                    }
                });
                HookLogger.logOnce("face-tool-b-hook", TAG, "FaceTool$a.b 底脸缓存捕获已接管");
            }
        } catch (Throwable t) {
            HookLogger.log(TAG, "FaceTool$a.b 注入失败: " + t);
        }

        try {
            FaceCacheSync.syncIfNeeded();
        } catch (Throwable ignored) {
        }
    }

    private static void hookUserFaceBean(Class<?> userFaceBean) {
        if (!userFaceBeanHooked.compareAndSet(false, true)) {
            return;
        }
        HookLogger.logOnce("face-ufb-hook", TAG, "UserFaceBean 已可用，安装参数覆写");
        try {
            XposedHelpers.findAndHookMethod(userFaceBean, "getBodyEnable",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isFaceEnabled()) {
                                    return;
                                }

                                param.setResult(false);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "getBodyEnable 回调失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("face-body", TAG, "UserFaceBean.getBodyEnable -> false（跳过活体动作）");
        } catch (Throwable t) {
            HookLogger.log(TAG, "getBodyEnable 注入失败: " + t);
        }
        try {
            XposedHelpers.findAndHookMethod(userFaceBean, "getSimilarityValue",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isFaceEnabled()) {
                                    return;
                                }

                                param.setResult(0);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "getSimilarityValue 回调失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("face-threshold", TAG, "相似度阈值置为 0");
        } catch (Throwable t) {
            HookLogger.log(TAG, "getSimilarityValue 注入失败: " + t);
        }
        try {
            XposedHelpers.findAndHookMethod(userFaceBean, "getFaceModelType",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isFaceEnabled()) {
                                    return;
                                }
                                param.setResult(2);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "getFaceModelType 回调失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("face-model-type", TAG, "UserFaceBean.getFaceModelType -> 2（强制本地分析模式）");
        } catch (Throwable t) {
            HookLogger.log(TAG, "getFaceModelType 注入失败: " + t);
        }
    }

    private static Object buildTrackingInfo(Object sample) throws Exception {
        Constructor<?> ctor = findConstructor(sample.getClass());
        if (ctor == null) {
            return null;
        }
        File photo = pickPhoto();
        if (photo == null && ModuleConfig.isFaceCacheEnabled()) {
            photo = FaceCacheSync.syncIfNeeded();
        }
        if (photo == null) {
            if (!folderLogged) {
                folderLogged = true;
                HookLogger.logOnce("face-no-photo", TAG, "未找到底图库照片，本次核验保持原始相机帧");
            }
            return null;
        }
        return buildTrackingInfo(sample.getClass(), photo, ctor);
    }

    static Object buildTrackingInfo(Class<?> tiClass, File photo) throws Exception {
        Constructor<?> ctor = findConstructor(tiClass);
        if (ctor == null) {
            return null;
        }
        return buildTrackingInfo(tiClass, photo, ctor);
    }

    private static Object buildTrackingInfo(Class<?> tiClass, File photo, Constructor<?> ctor) throws Exception {
        Bitmap bmp = decodePhoto(photo);
        if (bmp == null) {
            return null;
        }
        facePhotoAvailable = true;
        Nv21Frame frame = bitmapToNV21(bmp);
        HookLogger.logOnce("face-photo-hit", TAG, "选取人脸图片: " + photo.getName() + " (" + frame.w + "x" + frame.h + ")");
        return ctor.newInstance(frame.data, frame.w, frame.h, 5, 0);
    }

    private static Object buildZeroFrame(Object sample) throws Exception {
        Constructor<?> ctor = findConstructor(sample.getClass());
        if (ctor == null) {
            return null;
        }
        return ctor.newInstance(new byte[1], 0, 0, 5, 0);
    }

    private static Constructor<?> findConstructor(Class<?> cls) {
        Constructor<?> ctor = tiCtorCache.get(cls);
        if (ctor != null) {
            return ctor;
        }
        for (Constructor<?> c : cls.getConstructors()) {
            Class<?>[] pt = c.getParameterTypes();
            if (pt.length == 5 && pt[0] == byte[].class && pt[1] == int.class
                    && pt[2] == int.class && pt[3] == int.class && pt[4] == int.class) {
                ctor = c;
                break;
            }
        }
        if (ctor != null) {
            tiCtorCache.put(cls, ctor);
        }
        return ctor;
    }

    static File pickPhoto() {
        List<File> dirs = new ArrayList<>();
        String uid = currentUserId();
        File[] roots = new File[]{
                new File("/data/data/" + TARGET_PKG + "/files/face"),
                new File("/sdcard/Android/data/" + TARGET_PKG + "/files/face"),
                new File("/sdcard/闪动校园/face")
        };
        for (File root : roots) {
            if (uid != null && uid.length() > 0) {
                dirs.add(new File(root, uid));
            }
            dirs.add(new File(root, "default"));
            dirs.add(root);
        }

        List<File> manualImgs = new ArrayList<>();
        for (File dir : dirs) {
            File[] files = dir.listFiles();
            if (files == null) continue;
            for (File f : files) {
                if (f.isFile() && isImage(f.getName()) && !"registered_auto.jpg".equalsIgnoreCase(f.getName())) {
                    manualImgs.add(f);
                }
            }
            if (!manualImgs.isEmpty()) {
                File selected = manualImgs.get(random.nextInt(manualImgs.size()));
                HookLogger.logOnce("face-pick-manual", TAG, "选用自选照片: " + selected.getName());
                return selected;
            }
        }

        for (File dir : dirs) {
            File autoFile = new File(dir, "registered_auto.jpg");
            if (autoFile.exists() && autoFile.length() > 10 * 1024L) {
                HookLogger.logOnce("face-pick-auto", TAG, "未检测到自选照片，降级选用保底注册底脸: " + autoFile.getName());
                return autoFile;
            }
        }
        return null;
    }

        private static String currentUserId() {
        ClassLoader loader = appClassLoader != null ? appClassLoader : LateBinder.getRuntimeClassLoader();
        if (loader == null) {
            return null;
        }
        try {

            Class<?> ti9 = XposedHelpers.findClassIfExists("com.zj.adlib.ti9", loader);
            if (ti9 != null) {
                Object info = XposedHelpers.callStaticMethod(ti9, "c");
                if (info != null) {
                    Object uid = XposedHelpers.callMethod(info, "getUserId");
                    if (uid != null && String.valueOf(uid).length() > 0) {
                        return String.valueOf(uid);
                    }
                }
            }
        } catch (Throwable ignored) {
        }
        return null;
    }

    private static boolean isImage(String name) {
        String lower = name.toLowerCase();
        return lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png")
                || lower.endsWith(".bmp") || lower.endsWith(".webp");
    }

    private static Bitmap decodePhoto(File photo) {
        try {
            BitmapFactory.Options bounds = new BitmapFactory.Options();
            bounds.inJustDecodeBounds = true;
            BitmapFactory.decodeFile(photo.getAbsolutePath(), bounds);
            if (bounds.outWidth <= 0 || bounds.outHeight <= 0) {
                return null;
            }
            int maxSide = Math.max(bounds.outWidth, bounds.outHeight);
            int sample = 1;
            while (maxSide / (sample * 2) >= 1600) {
                sample *= 2;
            }
            BitmapFactory.Options opts = new BitmapFactory.Options();
            opts.inSampleSize = sample;
            Bitmap src = BitmapFactory.decodeFile(photo.getAbsolutePath(), opts);
            if (src == null) {
                return null;
            }
            HookLogger.logOnce("face-photo-" + photo.getName(), TAG, "注入人脸图片: " + photo.getName());
            return src;
        } catch (Throwable t) {
            HookLogger.log(TAG, "解码失败 " + photo.getName() + ": " + t);
            return null;
        }
    }

    private static final class Nv21Frame {
        final byte[] data;
        final int w;
        final int h;

        Nv21Frame(byte[] data, int w, int h) {
            this.data = data;
            this.w = w;
            this.h = h;
        }
    }

    private static Nv21Frame bitmapToNV21(Bitmap src) {
        Bitmap src2 = src;
        int w = src.getWidth();
        int h = src.getHeight();
        int maxSide = Math.max(w, h);
        if (maxSide > 1000) {
            float s = 1000.0f / maxSide;
            int dw = Math.max(1, Math.round(w * s));
            int dh = Math.max(1, Math.round(h * s));
            Bitmap scaled = Bitmap.createScaledBitmap(src2, dw, dh, true);
            if (scaled != src2) {
                src.recycle();
            }
            src2 = scaled;
            w = dw;
            h = dh;
        }
        if ((w & 1) != 0) w--;
        if ((h & 1) != 0) h--;
        int[] pixels = new int[w * h];
        src2.getPixels(pixels, 0, w, 0, 0, w, h);
        byte[] yuv = new byte[(w * h * 3) / 2];
        for (int y = 0; y < h; y++) {
            int row = y * w;
            for (int x = 0; x < w; x++) {
                int p = pixels[row + x];
                int r = (p >> 16) & 0xFF;
                int g = (p >> 8) & 0xFF;
                int b = p & 0xFF;
                int Y = ((66 * r + 129 * g + 25 * b + 128) >> 8) + 16;
                yuv[row + x] = (byte) (Y < 0 ? 0 : (Y > 255 ? 255 : Y));
            }
        }
        int uvIndex = w * h;
        for (int y = 0; y < h; y += 2) {
            int row0 = y * w;
            int row1 = (y + 1) * w;
            for (int x = 0; x < w; x += 2) {
                int p00 = pixels[row0 + x];
                int p01 = pixels[row0 + x + 1];
                int p10 = pixels[row1 + x];
                int p11 = pixels[row1 + x + 1];
                int r = (((p00 >> 16) & 0xFF) + ((p01 >> 16) & 0xFF) + ((p10 >> 16) & 0xFF) + ((p11 >> 16) & 0xFF)) / 4;
                int g = (((p00 >> 8) & 0xFF) + ((p01 >> 8) & 0xFF) + ((p10 >> 8) & 0xFF) + ((p11 >> 8) & 0xFF)) / 4;
                int b = ((p00 & 0xFF) + (p01 & 0xFF) + (p10 & 0xFF) + (p11 & 0xFF)) / 4;
                int U = ((-38 * r - 74 * g + 112 * b + 128) >> 8) + 128;
                int V = ((112 * r - 94 * g - 18 * b + 128) >> 8) + 128;
                yuv[uvIndex] = (byte) (V < 0 ? 0 : (V > 255 ? 255 : V));
                yuv[uvIndex + 1] = (byte) (U < 0 ? 0 : (U > 255 ? 255 : U));
                uvIndex += 2;
            }
        }
        return new Nv21Frame(yuv, w, h);
    }
}
