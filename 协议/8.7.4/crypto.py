"""
闪动校园 (v8.7.4) 密码学加解密实现
"""

import base64
import hashlib
import json
from typing import Optional, Union, Dict, Any
from Crypto.Cipher import AES, DES
from Crypto.Util.Padding import pad, unpad


APP_VERSION = "8.7.4"
BUILD_VERSION = "26093017"
APP_CODE = "SD001"

# 核心密钥配置
AES_SIGN_KEY = b"RHXL092CDOYTQJVP" + bytes(16)   # 动态请求签名密钥 (32 字节)
AES_FIELD_KEY = b"F44B0282BEA83557" + bytes(16)  # 密码及敏感字段加解密密钥 (32 字节)
AES_IV = b"01234ABCDEF56789"                     # AES-CBC 初始向量 (16 字节)
SLIDER_KEY = b"Ukp3hmSe7BmMcgbE"                 # 滑块拼图坐标密钥 (16 字节)
RUN_IMG_RECORD_KEY = "2V8BQ8MYXWU10Y9Z"         # 跑步防篡改静态盐值

# 多媒体资源解密 DES 密钥组
DES_KEYS = [
    b"c6bd901f", b"0ddf44be", b"950e5927", b"6460d8df",
    b"11fb887f", b"117e4900", b"bd113950", b"a99f6f97",
]


def aes_cbc_encrypt(data: Union[str, bytes], key: bytes = AES_SIGN_KEY, iv: bytes = AES_IV) -> str:
    """AES-256-CBC 加密 -> Base64 编码字符串"""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(raw, AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")


def aes_cbc_decrypt(cipher_b64: str, key: bytes = AES_SIGN_KEY, iv: bytes = AES_IV) -> str:
    """Base64 解码 -> AES-256-CBC 解密 -> UTF-8 字符串"""
    try:
        raw_cipher = base64.b64decode(cipher_b64)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(raw_cipher), AES.block_size)
        return decrypted.decode("utf-8")
    except Exception:
        return cipher_b64


def encrypt_password(password: str) -> str:
    """登录密码加密"""
    return aes_cbc_encrypt(password, key=AES_FIELD_KEY, iv=AES_IV)


def decrypt_password(cipher_b64: str) -> str:
    """登录密码解密还原"""
    return aes_cbc_decrypt(cipher_b64, key=AES_FIELD_KEY, iv=AES_IV)


def encrypt_field(plain_text: str) -> str:
    """敏感业务字段加密 (手机号/姓名/学号/学校等)"""
    return aes_cbc_encrypt(plain_text, key=AES_FIELD_KEY, iv=AES_IV)


def decrypt_field(cipher_b64: str) -> str:
    """敏感业务字段解密"""
    return aes_cbc_decrypt(cipher_b64, key=AES_FIELD_KEY, iv=AES_IV)


def get_sign(raw_body_text_or_dict: Union[str, Dict[str, Any]]) -> str:
    """
    计算官方 HTTP 请求头 sign:
    1. 请求体紧凑序列化 JSON 
    2. 计算 SHA-256 64 位小写哈希
    3. 首尾 8 字符换位重排: hex[-8:] + hex[8:-8] + hex[:8]
    4. 使用 AES_SIGN_KEY 与 AES_IV 执行 AES-256-CBC 加密后转 Base64
    """
    if isinstance(raw_body_text_or_dict, dict):
        clean_dict = {k: v for k, v in raw_body_text_or_dict.items() if k != "sign"}
        text = json.dumps(clean_dict, separators=(",", ":"), ensure_ascii=False)
    else:
        text = str(raw_body_text_or_dict)

    sha = hashlib.sha256(text.encode("utf-8")).hexdigest().lower()
    swapped = sha[-8:] + sha[8:-8] + sha[:8]
    return aes_cbc_encrypt(swapped, key=AES_SIGN_KEY, iv=AES_IV)


def encrypt_slider_point(raw_x: float, y: float = 15.0) -> str:
    """
    滑块拼图坐标加密:
    1. 减去基础图片边距 6.5 取整
    2. 加上协议位移补偿 16.5
    3. 构造坐标字典后经 AES-128-ECB 加密转 Base64
    """
    e_real = int(raw_x - 6.5)
    fake_e = e_real + 16.5
    data = {"x": fake_e, "y": int(y)}
    raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
    cipher = AES.new(SLIDER_KEY, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(raw, AES.block_size))).decode("utf-8")


def decrypt_slider_point(cipher_b64: str) -> Optional[Dict[str, Any]]:
    """滑块拼图坐标解密还原"""
    try:
        raw = base64.b64decode(cipher_b64)
        cipher = AES.new(SLIDER_KEY, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(raw), AES.block_size).decode("utf-8")
        return json.loads(decrypted)
    except Exception:
        return None


def calculate_run_img_record(
    run_record_code: str,
    timestamp_str: str,
    build_version: str = BUILD_VERSION,
    app_version: str = APP_VERSION
) -> str:
    """
    跑步防篡改结算值计算:
    MD5(runRecordCode + buildVersion + appVersion + RUN_IMG_RECORD_KEY + timestamp)
    """
    raw_str = f"{run_record_code}{build_version}{app_version}{RUN_IMG_RECORD_KEY}{timestamp_str}"
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest().lower()


def des_decrypt(encrypted_b64: str, r_index: int) -> Optional[str]:
    """多媒体 DES 资源文件解密"""
    try:
        key = DES_KEYS[r_index % len(DES_KEYS)]
        cipher = DES.new(key, DES.MODE_ECB)
        data = base64.b64decode(encrypted_b64)
        return unpad(cipher.decrypt(data), DES.block_size).decode("utf-8")
    except Exception:
        return None