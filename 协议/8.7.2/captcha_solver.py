"""
极验/AJ-Captcha 滑块拼图缺口求解器
基于 OpenCV Canny 边缘检测与模板匹配，求解滑块位移量 X。
"""

from typing import Optional


def solve_slider_notch(bg_bytes: bytes, tmpl_bytes: bytes) -> float:
    """
    通过图像边缘匹配算法求解滑块缺口偏移量 X
    :param bg_bytes: 背景图图片字节
    :param tmpl_bytes: 拼图滑块图片字节
    :return: 滑块向右位移量 (像素)
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        # 未安装 OpenCV 或 numpy 时的保底估算
        return 120.0

    try:
        bg_img = cv2.imdecode(np.frombuffer(bg_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
        tmpl_img = cv2.imdecode(np.frombuffer(tmpl_bytes, np.uint8), cv2.IMREAD_UNCHANGED)

        # 提取 Alpha 通道有效轮廓区域
        if len(tmpl_img.shape) >= 3 and tmpl_img.shape[2] == 4:
            alpha = tmpl_img[:, :, 3]
            pts = np.argwhere(alpha > 0)
            if pts.size == 0:
                return 100.0
            y_min, x_min = pts.min(axis=0)
            y_max, x_max = pts.max(axis=0) + 1
            mask = (alpha > 0).astype(np.uint8) * 255
            tmpl_roi = mask[y_min:y_max, x_min:x_max]
        else:
            y_min, y_max = 0, tmpl_img.shape[0]
            tmpl_roi = cv2.cvtColor(tmpl_img, cv2.COLOR_BGR2GRAY) if len(tmpl_img.shape) >= 3 else tmpl_img

        bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY) if len(bg_img.shape) >= 3 else bg_img

        # 截取横向匹配带
        y_start = max(0, y_min - 2)
        y_end = min(bg_gray.shape[0], y_max + 2)
        bg_band = bg_gray[y_start:y_end, :]

        bg_band_edges = cv2.Canny(bg_band, 50, 150)
        tmpl_edges = cv2.Canny(tmpl_roi, 50, 150)

        res = cv2.matchTemplate(bg_band_edges, tmpl_edges, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(res)

        notch_x = float(max_loc[0])
        # H5 端验证留白偏置补偿 +10.0
        return notch_x + 10.0
    except Exception:
        return 120.0
