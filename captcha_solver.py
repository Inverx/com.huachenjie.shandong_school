import cv2
import numpy as np
import base64
import json
from typing import Tuple, Dict, Any
import crypto

def solve_slider_notch(bg_bytes: bytes, tmpl_bytes: bytes) -> float:
    # 1. Decode images from bytes
    bg_img = cv2.imdecode(np.frombuffer(bg_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    tmpl_img = cv2.imdecode(np.frombuffer(tmpl_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    
    # 2. Extract valid bounding box from alpha channel
    alpha = tmpl_img[:, :, 3]
    pts = np.argwhere(alpha > 0)
    y_min, x_min = pts.min(axis=0)
    y_max, x_max = pts.max(axis=0) + 1
    
    mask = (alpha > 0).astype(np.uint8) * 255
    bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY) if len(bg_img.shape) >= 3 else bg_img
    
    # 3. Restrict template matching to the horizontal band [y_min-2 : y_max+2]
    y_start = max(0, y_min - 2)
    y_end = min(bg_gray.shape[0], y_max + 2)
    bg_band = bg_gray[y_start:y_end, :]
    
    bg_band_edges = cv2.Canny(bg_band, 50, 150)
    tmpl_edges = cv2.Canny(mask[y_min:y_max, x_min:x_max], 50, 150)
    
    res = cv2.matchTemplate(bg_band_edges, tmpl_edges, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_l = cv2.minMaxLoc(res)
    
    notch_x = float(max_l[0])
    # In H5 (CaptchaVerifyPage.js), the canvas adds +10.0 padding
    x_to_send = notch_x + 10.0
    return x_to_send

