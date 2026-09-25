package caom.inverx.huachenjie;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicBoolean;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

final class LateBinder {

    private static final String TAG = "[LateBinder]";

    private static final AtomicBoolean activityHooked = new AtomicBoolean(false);
    private static final List<Action> actions = new CopyOnWriteArrayList<>();
    private static volatile ClassLoader runtimeClassLoader;

    interface Action {
        boolean tryInstall(ClassLoader loader);
    }

    static void bind(XC_LoadPackage.LoadPackageParam lpparam, Action action) {
        actions.add(action);
        ensureActivityHook(lpparam.classLoader);
    }

    static ClassLoader getRuntimeClassLoader() {
        return runtimeClassLoader;
    }

    private static void ensureActivityHook(final ClassLoader appLoader) {
        if (!activityHooked.compareAndSet(false, true)) {
            return;
        }
        try {
            XposedHelpers.findAndHookMethod("android.app.Activity", appLoader,
                    "onCreate", "android.os.Bundle",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            try {
                                onActivity(param);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "Activity 回调失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("late-binder-activity", TAG, "Activity.onCreate 观察器已安装");
        } catch (Throwable t) {
            activityHooked.set(false);
            HookLogger.log(TAG, "Activity 监听注入失败: " + t);
        }
    }

    private static void onActivity(XC_MethodHook.MethodHookParam param) {
        Object activity = param.thisObject;
        if (activity == null) {
            return;
        }
        Class<?> cls = activity.getClass();
        if (!cls.getName().startsWith("com.huachenjie")) {
            return;
        }
        ClassLoader loader = cls.getClassLoader();
        if (loader == null) {
            return;
        }
        if (runtimeClassLoader != loader) {
            runtimeClassLoader = loader;
            FaceHook.setAppClassLoader(loader);
            FaceAutoHook.setAppClassLoader(loader);
            HookLogger.logOnce("runtime-loader-sync", TAG, "业务类加载器已同步");
        }
        for (Action action : actions) {
            try {
                if (action.tryInstall(loader)) {
                    actions.remove(action);
                }
            } catch (Throwable t) {
                HookLogger.log(TAG, "延迟绑定执行失败: " + t);
            }
        }
    }
}
