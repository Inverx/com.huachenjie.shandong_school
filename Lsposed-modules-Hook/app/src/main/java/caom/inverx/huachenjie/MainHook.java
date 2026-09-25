package caom.inverx.huachenjie;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class MainHook implements IXposedHookLoadPackage {

    private static final String TARGET_PACKAGE = "com.huachenjie.shandong_school";

    @Override
    public void handleLoadPackage(XC_LoadPackage.LoadPackageParam lpparam) throws Throwable {
        if (!TARGET_PACKAGE.equals(lpparam.packageName)) {
            return;
        }
        if (!TARGET_PACKAGE.equals(lpparam.processName)) {
            return;
        }

        HookLogger.log("[MainHook]", "进程注入: " + lpparam.processName);

        try {
            KeyAuditHook.install(lpparam);
        } catch (Throwable t) {
            HookLogger.log("[MainHook]", "KeyAudit 模块加载失败: " + t);
        }

        try {
            WifiHook.install(lpparam);
        } catch (Throwable t) {
            HookLogger.log("[MainHook]", "WiFi 模块加载失败: " + t);
        }
        try {
            FakeLocationHook.install(lpparam);
        } catch (Throwable t) {
            HookLogger.log("[MainHook]", "定位模块加载失败: " + t);
        }
        try {
            FaceHook.install(lpparam);
        } catch (Throwable t) {
            HookLogger.log("[MainHook]", "人脸模块加载失败: " + t);
        }
        try {
            FaceAutoHook.install(lpparam);
        } catch (Throwable t) {
            HookLogger.log("[MainHook]", "自动核验模块加载失败: " + t);
        }

        HookLogger.log("[MainHook]", "核心模块加载完成");
    }
}
