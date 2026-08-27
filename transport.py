import json
import time
import base64
import subprocess
import requests
from typing import Dict, Any, Optional
import crypto

DEFAULT_DEVICE_ID = "7a3f91c2d8e64b5fa104ce7392bd6e81"    #安卓id
DEFAULT_MODEL_NAME = "SM|SM-A5460"   #设备型号
DEFAULT_SYS_VER = "15"
DEFAULT_APP_VER = "8.6.8"
DEFAULT_BUILD_VER = "26082519"
DEFAULT_CHANNEL = "other"
DEFAULT_APP_CODE = "SD001"
ADB_DEFAULT_PATH = r"D:\Android\Sdk\platform-tools\adb.exe"

class HttpTransport:
    def __init__(self, 
                 base_url: str = "https://api.huachenjie.com",
                 use_adb: bool = True,
                 adb_path: str = ADB_DEFAULT_PATH,
                 device_id: str = DEFAULT_DEVICE_ID,
                 model_name: str = DEFAULT_MODEL_NAME,
                 system_version: str = DEFAULT_SYS_VER,
                 app_version: str = DEFAULT_APP_VER,
                 build_version: str = DEFAULT_BUILD_VER,
                 channel: str = DEFAULT_CHANNEL,
                 app_code: str = DEFAULT_APP_CODE,
                 sign_key: str = crypto.KEY_DEFAULT_SIGN):
        self.base_url = base_url.rstrip('/')
        self.use_adb = use_adb
        self.adb_path = adb_path
        self.device_id = device_id
        self.model_name = model_name
        self.system_version = system_version
        self.app_version = app_version
        self.build_version = build_version
        self.channel = channel
        self.app_code = app_code
        self.sign_key = sign_key
        
        self.token: Optional[str] = None
        self.satoken: Optional[str] = None
        self.session = requests.Session()
        self.user_agent = f"ShanDong/{self.app_version} (lge;Android {self.system_version})"

    def _exec_adb_shell(self, cmd_str: str) -> bytes:
        p = subprocess.Popen([self.adb_path, "shell", cmd_str], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = p.communicate()
        return out

    def get_common_params(self) -> Dict[str, Any]:
        return {
            "modelName": self.model_name,
            "appVersion": self.app_version,
            "buildVersion": self.build_version,
            "channel": self.channel,
            "appCode": self.app_code,
            "deviceId": self.device_id,
            "systemVersion": self.system_version,
            "platform": "2",
            "timestamp": str(int(time.time() * 1000))
        }

    def post(self, path: str, extra_params: Optional[Dict[str, Any]] = None, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        payload = self.get_common_params()
        if extra_params:
            payload.update(extra_params)
        
        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        sign_header = crypto.compute_sign(payload_str, self.sign_key)
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": self.user_agent,
            "sign": sign_header,
            "Connection": "Keep-Alive"
        }
        if self.token:
            headers["Authorization"] = self.token
        if self.satoken:
            headers["satoken"] = self.satoken
        if extra_headers:
            headers.update(extra_headers)

        if self.use_adb:
            b64_body = base64.b64encode(payload_str.encode('utf-8')).decode('utf-8')
            self._exec_adb_shell(f"echo {b64_body} | base64 -d > /data/local/tmp/api_req.json")
            
            h_args = []
            for k, v in headers.items():
                v_esc = v.replace('"', '\\"')
                h_args.append(f'-H "{k}: {v_esc}"')
            
            curl_cmd = f'curl -s --compressed -X POST "{url}" {" ".join(h_args)} --data-binary @/data/local/tmp/api_req.json'
            raw_out = self._exec_adb_shell(curl_cmd).decode('utf-8', errors='ignore')
            try:
                return json.loads(raw_out)
            except Exception:
                return {"error": -1, "message": "解析响应失败", "raw": raw_out}
        else:
            try:
                resp = self.session.post(url, data=payload_str.encode('utf-8'), headers=headers, timeout=15)
                return resp.json()
            except Exception as e:
                return {"error": -1, "message": str(e)}

