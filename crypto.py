import base64
import hashlib
from Crypto.Cipher import AES

# Key constants extracted from app reverse engineering
KEY_DEFAULT_SIGN = "F44B0282BEA83557"
IV_DEFAULT = "01234ABCDEF56789"
KEY_CAPTCHA_POINT = "Ukp3hmSe7BmMcgbE"
BUILD_VERSION = "26082519"
APP_VERSION = "8.6.8"

def _pad_key(key_str: str) -> bytes:
    # Java cq.f: fills key with 0x00 up to 32 bytes for AES-256
    k = key_str.encode("utf-8")
    if len(k) == 32:
        return k
    return k.ljust(32, b"\x00")[:32]

def h58_sha256_reorder(json_str: str) -> str:
    # Java h58.c: computes SHA-256 hex string and swaps first 8 and last 8 characters
    if not json_str:
        return ""
    h = hashlib.sha256(json_str.encode("utf-8")).hexdigest().lower()
    if len(h) < 16:
        return h
    return h[-8:] + h[8:-8] + h[:8]

def aes_cbc_encrypt(plain_text: str, key_str: str = KEY_DEFAULT_SIGN, iv_str: str = IV_DEFAULT) -> str:
    # Java cq.c: AES/CBC/PKCS7Padding -> Base64
    key = _pad_key(key_str)
    iv = iv_str.encode("utf-8")
    raw = plain_text.encode("utf-8")
    pad = 16 - (len(raw) % 16)
    raw += bytes([pad] * pad)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    enc = cipher.encrypt(raw)
    return base64.b64encode(enc).decode("utf-8")

def aes_cbc_decrypt(cipher_b64: str, key_str: str = KEY_DEFAULT_SIGN, iv_str: str = IV_DEFAULT) -> str:
    # Java cq.a: Base64 -> AES/CBC/PKCS7Padding Decrypt
    try:
        key = _pad_key(key_str)
        iv = iv_str.encode("utf-8")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        raw = base64.b64decode(cipher_b64)
        dec = cipher.decrypt(raw)
        pad = dec[-1]
        if 1 <= pad <= 16:
            dec = dec[:-pad]
        return dec.decode("utf-8", errors="ignore")
    except Exception:
        return cipher_b64

def compute_sign(json_str: str, key_str: str = KEY_DEFAULT_SIGN) -> str:
    # Computes HTTP Header "sign"
    reordered_hash = h58_sha256_reorder(json_str)
    return aes_cbc_encrypt(reordered_hash, key_str, IV_DEFAULT)

def encrypt_field(plain_str: str) -> str:
    # Encrypts sensitive fields (password, phone, schoolName)
    return aes_cbc_encrypt(plain_str, KEY_DEFAULT_SIGN, IV_DEFAULT)

def decrypt_field(cipher_b64: str) -> str:
    # Decrypts sensitive fields returned by server
    return aes_cbc_decrypt(cipher_b64, KEY_DEFAULT_SIGN, IV_DEFAULT)

def encrypt_captcha_point(x: float, y: float = 15.0, secret_key: str = KEY_CAPTCHA_POINT) -> str:
    # Encrypts slider coordinates with AES-128-ECB for AJ-Captcha verification
    import json
    point_dict = {"x": float(x), "y": int(y)}
    raw = json.dumps(point_dict, separators=(",", ":")).encode("utf-8")
    pad = 16 - (len(raw) % 16)
    raw += bytes([pad] * pad)
    cipher = AES.new(secret_key.encode("utf-8"), AES.MODE_ECB)
    enc = cipher.encrypt(raw)
    return base64.b64encode(enc).decode("utf-8")

def compute_run_img_record(run_record_code: str, sign_key: str, timestamp_str: str) -> str:
    # Anti-tamper checksum: MD5(runRecordCode + buildVersion + appVersion + key + timestamp)
    raw_str = f"{run_record_code}{BUILD_VERSION}{APP_VERSION}{sign_key}{timestamp_str}"
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest().lower()

