"""
闪动校园 8.7.2 — 网络传输层 (HttpTransport)
支持三种网络模式：
1. "direct" (默认): 纯 Python requests / curl_cffi 直连服务器
2. "proxy": 指定 HTTP/HTTPS 代理访问
3. "adb": 通过 ADB shell curl 调用手机蜂窝网络传输 (解决部分地区 PC 端 IP 拦截)
"""

import json
import os
import random
import secrets
import shutil
import subprocess
import tempfile
import time
import urllib.parse
from typing import Dict, Any, Optional

import requests

from crypto import get_sign, APP_VERSION, BUILD_VERSION, APP_CODE


def generate_device_id() -> str:
    """生成符合 Android ID 格式的 16 位小写十六进制字符串"""
    return secrets.token_hex(8)


class HttpTransport:
    DEFAULT_BASE_URL = "https://api.huachenjie.com/run-front"
    DEFAULT_MODEL = "SM-A5460"
    DEFAULT_SYS_VER = "14"
    DEFAULT_PLATFORM = "2"
    DEFAULT_CHANNEL = "other"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        token: Optional[str] = None,
        satoken: Optional[str] = None,
        device_id: Optional[str] = None,
        model_name: Optional[str] = None,
        system_version: Optional[str] = None,
        transport_mode: str = "direct",
        proxy: Optional[str] = None,
        adb_path: Optional[str] = None,
        timeout: int = 15
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token or ""
        self.satoken = satoken or ""
        self.device_id = device_id or os.environ.get("SHANDONG_DEVICE_ID") or generate_device_id()
        self.model_name = model_name or os.environ.get("SHANDONG_MODEL") or self.DEFAULT_MODEL
        self.system_version = system_version or self.DEFAULT_SYS_VER
        self.app_version = APP_VERSION
        self.build_version = BUILD_VERSION
        self.app_code = APP_CODE
        self.platform = self.DEFAULT_PLATFORM
        self.channel = self.DEFAULT_CHANNEL
        self.transport_mode = transport_mode
        self.proxy = proxy or os.environ.get("SHANDONG_PROXY")
        self.timeout = timeout

        # ADB 路径解析 (优先参数 -> 环境变量 -> 系统 PATH)
        self.adb_path = adb_path or os.environ.get("ADB_PATH") or shutil.which("adb") or "adb"

        # 初始化 requests 会话
        self.session = requests.Session()
        if self.proxy and self.transport_mode == "proxy":
            self.session.proxies = {"http": self.proxy, "https": self.proxy}

    def build_base_payload(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """构建官方公共请求体参数"""
        payload = {
            "modelName": self.model_name,
            "appVersion": self.app_version,
            "buildVersion": self.build_version,
            "channel": self.channel,
            "appCode": self.app_code,
            "deviceId": self.device_id,
            "systemVersion": self.system_version,
            "platform": self.platform,
            "timestamp": str(int(time.time() * 1000)),
        }
        if extra:
            payload.update(extra)
        return payload

    def build_headers(self, v_param: Optional[str] = None, api_module: Optional[str] = None) -> Dict[str, str]:
        """构建官方请求头，计算并包含 token 与业务参数"""
        brand = self.model_name.split("|")[0].split("-")[0].lower()
        headers = {
            "Host": "api.huachenjie.com",
            "Connection": "Keep-Alive",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": f"ShanDong/{self.app_version} ({brand};Android {self.system_version})",
            "Accept-Encoding": "gzip",
            "app": "run-front",
            "Authorization": self.token,
            "satoken": self.satoken,
            "e": "0",
            "pv": "2",
            "k": "",
        }
        if v_param:
            headers["v"] = v_param
        if api_module:
            headers["api"] = api_module
        return headers

    def post(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        v_param: Optional[str] = None,
        api_module: Optional[str] = None
    ) -> Dict[str, Any]:
        """统一发送签名 POST 请求"""
        clean_endpoint = endpoint.lstrip("/")
        if clean_endpoint.startswith("run-front/"):
            clean_endpoint = clean_endpoint[len("run-front/"):]
        url = f"{self.base_url}/{clean_endpoint}"

        data_dict = payload or {}
        # 排除已有的 sign 字段，生成紧凑 JSON
        clean_payload = {k: v for k, v in data_dict.items() if k != "sign"}
        body_json = json.dumps(clean_payload, separators=(",", ":"), ensure_ascii=False)

        headers = self.build_headers(v_param, api_module)
        headers["sign"] = get_sign(body_json)

        if self.transport_mode == "adb":
            return self._adb_post(url, headers, body_json)
        return self._http_post(url, headers, body_json)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """统一发送 GET 请求 (如 syncTime 等接口)"""
        clean_endpoint = endpoint.lstrip("/")
        if clean_endpoint.startswith("run-front/"):
            clean_endpoint = clean_endpoint[len("run-front/"):]
        url = f"{self.base_url}/{clean_endpoint}"

        if params:
            qs = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items())
            url = f"{url}?{qs}"

        headers = {
            "Host": "api.huachenjie.com",
            "Connection": "Keep-Alive",
            "User-Agent": "okhttp/4.9.0",
            "Accept-Encoding": "gzip",
        }

        if self.transport_mode == "adb":
            return self._adb_get(url, headers)
        return self._http_get(url, headers)

    def _http_post(self, url: str, headers: Dict[str, str], body_str: str) -> Dict[str, Any]:
        """Python requests HTTP POST"""
        try:
            resp = self.session.post(
                url,
                data=body_str.encode("utf-8"),
                headers=headers,
                timeout=self.timeout
            )
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"code": -1, "message": f"网络请求失败: {str(e)}"}
        except json.JSONDecodeError:
            return {"code": -1, "message": "服务端返回非合法 JSON"}

    def _http_get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Python requests HTTP GET"""
        try:
            resp = self.session.get(url, headers=headers, timeout=self.timeout)
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"code": -1, "message": f"网络请求失败: {str(e)}"}
        except json.JSONDecodeError:
            return {"code": -1, "message": "服务端返回非合法 JSON"}

    def _adb_post(self, url: str, headers: Dict[str, str], body_str: str) -> Dict[str, Any]:
        """通过 ADB Shell curl 发送 POST 请求"""
        local_tmp = os.path.join(tempfile.gettempdir(), f"sd_req_{secrets.token_hex(4)}.json")
        remote_tmp = "/data/local/tmp/sd_body.json"

        try:
            with open(local_tmp, "wb") as f:
                f.write(body_str.encode("utf-8"))

            # 推送请求体至手机临时目录
            subprocess.run(
                [self.adb_path, "push", local_tmp, remote_tmp],
                capture_output=True, timeout=5, encoding="utf-8", errors="replace"
            )

            # 组装 curl 参数
            h_args = []
            for k, v in headers.items():
                if not v and k != "k":
                    continue
                safe_v = str(v).replace("'", "'\\''")
                h_args.append(f"-H '{k}: {safe_v}'")

            header_str = " ".join(h_args)
            curl_cmd = (
                f"curl -s -k --compressed -X POST '{url}' "
                f"{header_str} -d @{remote_tmp} --connect-timeout {self.timeout}"
            )

            res = subprocess.run(
                [self.adb_path, "shell", curl_cmd],
                capture_output=True, timeout=self.timeout + 10, encoding="utf-8", errors="replace"
            )

            out = res.stdout.strip()
            if not out:
                return {"code": -1, "message": f"ADB curl 返回空响应: {res.stderr.strip()}"}
            return json.loads(out)
        except Exception as e:
            return {"code": -1, "message": f"ADB 执行异常: {str(e)}"}
        finally:
            if os.path.exists(local_tmp):
                try:
                    os.remove(local_tmp)
                except Exception:
                    pass

    def _adb_get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """通过 ADB Shell curl 发送 GET 请求"""
        try:
            h_args = []
            for k, v in headers.items():
                safe_v = str(v).replace("'", "'\\''")
                h_args.append(f"-H '{k}: {safe_v}'")

            header_str = " ".join(h_args)
            curl_cmd = f"curl -s -k --compressed '{url}' {header_str} --connect-timeout {self.timeout}"

            res = subprocess.run(
                [self.adb_path, "shell", curl_cmd],
                capture_output=True, timeout=self.timeout + 10, encoding="utf-8", errors="replace"
            )
            out = res.stdout.strip()
            if not out:
                return {"code": -1, "message": f"ADB GET 返回空响应: {res.stderr.strip()}"}
            return json.loads(out)
        except Exception as e:
            return {"code": -1, "message": f"ADB 执行异常: {str(e)}"}
