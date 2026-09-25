package caom.inverx.huachenjie;

import android.app.Application;
import android.content.Context;
import android.util.Log;
import java.util.List;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class KeyAuditHook {
    private static final String TAG = "KEY_AUDIT";
    private static volatile boolean isHooked = false;

    public static void install(final XC_LoadPackage.LoadPackageParam lpparam) {
        Log.e(TAG, "挂载 Application 启动监听");

        XposedHelpers.findAndHookMethod(Application.class, "attach", Context.class, new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                Context context = (Context) param.args[0];
                ClassLoader classLoader = context.getClassLoader();
                Log.e(TAG, "[KeyAuditHook] Application.attach 完成，捕获到真实业务 ClassLoader: " + classLoader);
                hookBusinessClasses(classLoader);
            }
        });

        XposedHelpers.findAndHookMethod(ClassLoader.class, "loadClass", String.class, boolean.class, new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                String className = (String) param.args[0];
                if (!isHooked && ("com.zj.adlib.o34".equals(className) || "com.zj.adlib.a43".equals(className))) {
                    ClassLoader cl = (ClassLoader) param.thisObject;
                    Log.e(TAG, "[KeyAuditHook] 探测到目标类加载: " + className + ", 开始全面挂钩...");
                    hookBusinessClasses(cl);
                }
            }
        });
    }

    private static synchronized void hookBusinessClasses(ClassLoader classLoader) {
        if (isHooked) return;

        try {
            Class<?> o34Cls = XposedHelpers.findClass("com.zj.adlib.o34", classLoader);
            XposedHelpers.findAndHookMethod(o34Cls, "c", Context.class, int.class, new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    Log.e(TAG, "==================================================");
                    Log.e(TAG, ">>> [o34.c 命中] resId=" + param.args[1] + " => 动态返回签名密钥: [" + param.getResult() + "]");
                    Log.e(TAG, "==================================================");
                }
            });
            Log.e(TAG, "o34.c 注入成功");
        } catch (Throwable t) {
            Log.e(TAG, "[-] o34.c 寻找异常: " + t);
        }

        try {
            Class<?> kCls = XposedHelpers.findClass("com.huachenjie.c.K", classLoader);
            XposedHelpers.findAndHookMethod(kCls, "b2s", byte[].class, int.class, new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    byte[] bytes = (byte[]) param.args[0];
                    int type = (Integer) param.args[1];
                    Log.e(TAG, "==================================================");
                    Log.e(TAG, ">>> [K.b2s Native 命中] bytesLen=" + (bytes != null ? bytes.length : 0)
                            + ", type=" + type + " => 计算结果: [" + param.getResult() + "]");
                    Log.e(TAG, "==================================================");
                }
            });
            Log.e(TAG, "K.b2s 注入成功");
        } catch (Throwable t) {
            Log.e(TAG, "[-] K.b2s 寻找异常: " + t);
        }

        try {
            Class<?> a43Cls = XposedHelpers.findClass("com.zj.adlib.a43", classLoader);
            XposedHelpers.findAndHookMethod(a43Cls, "e", String.class, String.class, String.class, boolean.class, boolean.class, List.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    Log.e(TAG, "==================================================");
                    Log.e(TAG, ">>> [a43.e 全局配置 命中] key1(pwd)=" + param.args[0]
                            + ", key2(sign)=" + param.args[1]
                            + ", key3=" + param.args[2]
                            + ", debug=" + param.args[3]
                            + ", list=" + param.args[5]);
                    Log.e(TAG, "==================================================");
                }
            });
            Log.e(TAG, "a43.e 注入成功");
            isHooked = true;
        } catch (Throwable t) {
            Log.e(TAG, "[-] a43.e 寻找异常: " + t);
        }
    }
}
