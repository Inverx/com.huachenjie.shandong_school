package caom.inverx.huachenjie;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;

final class ClassWatch {

    private static final String TAG = "[ClassWatch]";

    private static final AtomicBoolean installed = new AtomicBoolean(false);
    private static final Map<String, Target> targets = new ConcurrentHashMap<>();

    private static final class Target {
        final AtomicBoolean done = new AtomicBoolean(false);
        volatile Callback callback;

        Target(Callback callback) {
            this.callback = callback;
        }
    }

    interface Callback {
        void onClassAvailable(Class<?> cls);
    }

    static void watch(String className, Callback callback) {
        if (className == null || callback == null) {
            return;
        }
        targets.put(className, new Target(callback));
        ensureInstalled();
    }

    private static void ensureInstalled() {
        if (!installed.compareAndSet(false, true)) {
            return;
        }
        try {
            XposedHelpers.findAndHookMethod(ClassLoader.class, "loadClass", String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            onLoad((String) param.args[0], param.getResult());
                        }
                    });
            XposedHelpers.findAndHookMethod(ClassLoader.class, "loadClass", String.class, boolean.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            onLoad((String) param.args[0], param.getResult());
                        }
                    });
            HookLogger.logOnce("class-watch-installed", TAG, "类加载观察器已安装");
        } catch (Throwable t) {
            installed.set(false);
            HookLogger.log(TAG, "loadClass 注入失败: " + t);
        }
    }

    private static void onLoad(String name, Object result) {
        if (name == null || name.length() == 0 || !(result instanceof Class)) {
            return;
        }
        Target target = targets.get(name);
        if (target == null || target.done.get()) {
            return;
        }
        if (target.done.compareAndSet(false, true)) {
            Callback callback = target.callback;
            target.callback = null;
            if (callback != null) {
                try {
                    callback.onClassAvailable((Class<?>) result);
                } catch (Throwable t) {
                    HookLogger.log(TAG, "回调执行失败: " + name + ": " + t);
                }
            }
        }
    }
}
