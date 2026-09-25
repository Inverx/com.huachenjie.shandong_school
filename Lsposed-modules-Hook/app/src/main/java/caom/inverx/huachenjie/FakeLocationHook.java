package caom.inverx.huachenjie;

import android.location.Location;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class FakeLocationHook {

    private static final String TAG = "[LocationHook]";
    private static final String BD_LOCATION = "com.baidu.location.BDLocation";
    private static final String HCJ_ADDRESS_INFO = "huachenjie.sdk.map.lib_base.HCJAddressInfo";
    private static final String CHEAT_COMPONENT = "com.huachenjie.running.component.CheatingDetectionComponent";

    private static final java.util.concurrent.atomic.AtomicBoolean bdLocationHooked =
            new java.util.concurrent.atomic.AtomicBoolean(false);
    private static final java.util.concurrent.atomic.AtomicBoolean hcjAddressHooked =
            new java.util.concurrent.atomic.AtomicBoolean(false);
    private static final java.util.concurrent.atomic.AtomicBoolean cheatComponentHooked =
            new java.util.concurrent.atomic.AtomicBoolean(false);

    static void install(XC_LoadPackage.LoadPackageParam lpparam) {
        HookLogger.logOnce("loc-install", TAG, "安装虚拟定位立体防御");

        hookSystemLocation();

        ClassWatch.watch(BD_LOCATION, new ClassWatch.Callback() {
            @Override
            public void onClassAvailable(Class<?> cls) {
                hookBDLocation(cls);
            }
        });

        try {
            XposedHelpers.findAndHookMethod("android.os.ServiceManager", lpparam.classLoader,
                    "getService", String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isLocationEnabled()) {
                                    return;
                                }
                                String name = (String) param.args[0];
                                if ("service_mock_location".equals(name) || "service_fl_ml".equals(name)) {
                                    param.setResult(null);
                                }
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "getService 处理失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("loc-service-manager", TAG, "拦截虚拟定位服务查询");
        } catch (Throwable t) {
            HookLogger.log(TAG, "ServiceManager 注入失败: " + t);
        }

        LateBinder.bind(lpparam, new LateBinder.Action() {
            @Override
            public boolean tryInstall(ClassLoader loader) {
                if (!bdLocationHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(BD_LOCATION, loader);
                    if (cls != null) {
                        hookBDLocation(cls);
                    }
                }
                if (!hcjAddressHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(HCJ_ADDRESS_INFO, loader);
                    if (cls != null) {
                        hookHCJAddressInfo(cls);
                    }
                }
                if (!cheatComponentHooked.get()) {
                    Class<?> cls = XposedHelpers.findClassIfExists(CHEAT_COMPONENT, loader);
                    if (cls != null) {
                        hookCheatingDetectionComponent(cls);
                    }
                }
                return bdLocationHooked.get() && hcjAddressHooked.get() && cheatComponentHooked.get();
            }
        });
    }

    private static void hookSystemLocation() {
        try {
            XposedHelpers.findAndHookMethod(Location.class, "isFromMockProvider", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (ModuleConfig.isLocationEnabled()) {
                        param.setResult(false);
                    }
                }
            });
            HookLogger.logOnce("loc-sys-mock", TAG, "isFromMockProvider 置为 false");
        } catch (Throwable t) {
            HookLogger.log(TAG, "isFromMockProvider 注入失败: " + t);
        }
        try {
            XposedHelpers.findAndHookMethod(Location.class, "isMock", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (ModuleConfig.isLocationEnabled()) {
                        param.setResult(false);
                    }
                }
            });
            HookLogger.logOnce("loc-sys-ismock", TAG, "isMock 置为 false");
        } catch (Throwable ignored) {

        }
    }

    private static void hookBDLocation(Class<?> bdLocation) {
        if (!bdLocationHooked.compareAndSet(false, true)) {
            return;
        }
        HookLogger.logOnce("loc-bd-ready", TAG, "BDLocation 已可用，安装 mock 归零");
        try {
            XposedHelpers.findAndHookMethod(bdLocation, "getMockGnssStrategy",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isLocationEnabled()) {
                                    return;
                                }
                                param.setResult(0);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "getMockGnssStrategy 处理失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("loc-strategy", TAG, "getMockGnssStrategy 置为 0");
        } catch (Throwable t) {
            HookLogger.log(TAG, "getMockGnssStrategy 注入失败: " + t);
        }
        try {
            XposedHelpers.findAndHookMethod(bdLocation, "getMockGnssProbability",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isLocationEnabled()) {
                                    return;
                                }
                                param.setResult(0);
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "getMockGnssProbability 处理失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("loc-probability", TAG, "getMockGnssProbability 置为 0");
        } catch (Throwable t) {
            HookLogger.log(TAG, "getMockGnssProbability 注入失败: " + t);
        }
    }

    private static void hookHCJAddressInfo(Class<?> hcjInfo) {
        if (!hcjAddressHooked.compareAndSet(false, true)) {
            return;
        }
        try {
            XposedHelpers.findAndHookMethod(hcjInfo, "isMock", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (ModuleConfig.isLocationEnabled()) {
                        param.setResult(false);
                    }
                }
            });
            XposedHelpers.findAndHookMethod(hcjInfo, "isFromMockProvider", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (ModuleConfig.isLocationEnabled()) {
                        param.setResult(false);
                    }
                }
            });
            HookLogger.logOnce("loc-hcj-mock", TAG, "HCJAddressInfo mock 标记置为 false");
        } catch (Throwable t) {
            HookLogger.log(TAG, "HCJAddressInfo 注入失败: " + t);
        }
    }

    private static void hookCheatingDetectionComponent(Class<?> cdcClass) {
        if (!cheatComponentHooked.compareAndSet(false, true)) {
            return;
        }
        try {

            XposedHelpers.findAndHookMethod(cdcClass, "f", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (ModuleConfig.isLocationEnabled()) {
                        param.setResult(null);
                    }
                }
            });
            XposedHelpers.findAndHookMethod(cdcClass, "e", java.util.Map.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (ModuleConfig.isLocationEnabled()) {
                        param.setResult(null);
                    }
                }
            });
            HookLogger.logOnce("loc-cdc-disabled", TAG, "CheatingDetectionComponent 30秒作弊定时上报已在源头阻断");
        } catch (Throwable t) {
            HookLogger.log(TAG, "CheatingDetectionComponent 注入失败: " + t);
        }
    }
}
