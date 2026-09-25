package caom.inverx.huachenjie;

import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.net.NetworkInfo;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class WifiHook {

    private static final String TAG = "[WiFiHook]";

    static void install(XC_LoadPackage.LoadPackageParam lpparam) {
        HookLogger.logOnce("wifi-install", TAG, "安装 WiFi 检测绕过");

        try {
            XposedHelpers.findAndHookMethod(NetworkCapabilities.class, "hasTransport", int.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            try {
                                if (!ModuleConfig.isWifiEnabled()) {
                                    return;
                                }
                                int transport = (Integer) param.args[0];
                                if (transport == NetworkCapabilities.TRANSPORT_WIFI) {
                                    param.setResult(false);
                                }
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "hasTransport 处理失败: " + t);
                            }
                        }
                    });
            HookLogger.logOnce("wifi-hasTransport", TAG, "拦截 WiFi 传输判定");
        } catch (Throwable t) {
            HookLogger.log(TAG, "hasTransport 注入失败: " + t);
        }

        try {
            XposedHelpers.findAndHookMethod(ConnectivityManager.class, "getActiveNetworkInfo",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (!ModuleConfig.isWifiEnabled()) {
                                return;
                            }
                            try {
                                NetworkInfo info = (NetworkInfo) param.getResult();
                                if (info != null && info.getType() == ConnectivityManager.TYPE_WIFI) {
                                    XposedHelpers.setIntField(info, "mNetworkType", ConnectivityManager.TYPE_MOBILE);
                                    XposedHelpers.setObjectField(info, "mTypeName", "MOBILE");
                                }
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "getActiveNetworkInfo 处理失败: " + t);
                            }
                        }
                    });
        } catch (Throwable t) {
            HookLogger.log(TAG, "getActiveNetworkInfo 注入失败: " + t);
        }

        try {
            XposedHelpers.findAndHookMethod(ConnectivityManager.class, "getNetworkCapabilities",
                    android.net.Network.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (!ModuleConfig.isWifiEnabled()) {
                                return;
                            }
                            try {
                                NetworkCapabilities caps = (NetworkCapabilities) param.getResult();
                                if (caps != null) {
                                    long transports = XposedHelpers.getLongField(caps, "mTransportTypes");
                                    if ((transports & (1L << NetworkCapabilities.TRANSPORT_WIFI)) != 0) {
                                        transports &= ~(1L << NetworkCapabilities.TRANSPORT_WIFI);
                                        transports |= (1L << NetworkCapabilities.TRANSPORT_CELLULAR);
                                        XposedHelpers.setLongField(caps, "mTransportTypes", transports);
                                    }
                                }
                            } catch (Throwable t) {
                                HookLogger.log(TAG, "getNetworkCapabilities 处理失败: " + t);
                            }
                        }
                    });
        } catch (Throwable t) {
            HookLogger.log(TAG, "getNetworkCapabilities 注入失败: " + t);
        }
    }
}
