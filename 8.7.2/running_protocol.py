"""
闪动校园 8.7.2 — 运动轨迹与生理指标高拟真生成引擎
1. 步频指标严格对齐官方标准：
   - stepInterval 设为 60 秒 (1分钟一档)
   - 每分钟步数自然高斯波动在 140 ~ 152 步 (精准对应 140~152 步/分钟)
2. 配速指标对齐官方：
   - paceInterval 设为 1000 米 (每公里一段，每公里用时约 340~365 秒)
3. 轨迹点对齐官方 RunLatLng 实体：
   - index, lat, lng, runTime, collectTime, createTime, satellites, accuracy, state, offFenceDisM
4. 电子围栏射线法 (Ray-casting PIP) 内部判定
"""

import math
import random
import time
from typing import List, Dict, Any, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算两点经纬度的大圆物理距离（米）"""
    r = 6378137.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2.0) ** 2
    return r * 2.0 * math.asin(math.sqrt(a))


def is_point_in_polygon(x: float, y: float, poly: List[Tuple[float, float]]) -> bool:
    """射线法判断点是否在多边形内部"""
    n = len(poly)
    if n < 3:
        return True
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def move_towards(curr_lng: float, curr_lat: float, target_lng: float, target_lat: float, step_distance: float):
    """朝目标点方向移动固定物理距离"""
    dist = haversine_distance(curr_lat, curr_lng, target_lat, target_lng)
    if dist <= step_distance or dist == 0:
        return target_lng, target_lat, dist
    ratio = step_distance / dist
    new_lng = curr_lng + (target_lng - curr_lng) * ratio
    new_lat = curr_lat + (target_lat - curr_lat) * ratio
    return new_lng, new_lat, step_distance


def generate_natural_sunrun_trajectory(
    fence_boundary: List[Dict[str, Any]],
    target_points: List[Dict[str, Any]],
    target_distance_m: float = 3010.0,
    avg_pace_sec_per_km: int = 358,
    start_timestamp_ms: int = None
) -> Dict[str, Any]:
    """
    生成高度拟真、符合官方校验的轨迹点流与分段指标
    """
    if not start_timestamp_ms:
        start_timestamp_ms = int(time.time() * 1000)

    # 1. 围栏多边形与中心点
    poly = [(float(p["lng"]), float(p["lat"])) for p in fence_boundary] if fence_boundary else []
    if poly:
        center_lng = sum(p[0] for p in poly) / len(poly)
        center_lat = sum(p[1] for p in poly) / len(poly)
    elif target_points:
        center_lng = float(target_points[0]["lng"])
        center_lat = float(target_points[0]["lat"])
        poly = [
            (center_lng - 0.002, center_lat - 0.002),
            (center_lng + 0.002, center_lat - 0.002),
            (center_lng + 0.002, center_lat + 0.002),
            (center_lng - 0.002, center_lat + 0.002)
        ]
    else:
        raise ValueError("生成轨迹失败：必须提供有效的校园围栏 (fence_boundary) 或打卡桩 (target_points)")

    # 2. 运动学常量：配速 350-360 秒/公里，采样周期 3.0 秒
    speed_mps = 1000.0 / avg_pace_sec_per_km
    sample_interval_s = 3.0
    base_cadence_spm = 144.0

    # 起点
    if target_points:
        curr_lng = float(target_points[0]["lng"]) + random.uniform(-0.00008, 0.00008)
        curr_lat = float(target_points[0]["lat"]) + random.uniform(-0.00008, 0.00008)
    else:
        curr_lng = center_lng + random.uniform(-0.0002, 0.0002)
        curr_lat = center_lat + random.uniform(-0.0002, 0.0002)

    # 路径规划目标队列
    route_goals = []
    for tp in target_points:
        route_goals.append({
            "lng": float(tp["lng"]),
            "lat": float(tp["lat"]),
            "code": tp.get("code")
        })
    route_goals.append({"lng": center_lng, "lat": center_lat, "code": "CRUISE"})

    current_goal_idx = 0
    passed_target_points = []
    for tp in target_points:
        passed_target_points.append({
            "code": tp["code"],
            "lng": float(tp["lng"]),
            "lat": float(tp["lat"]),
            "passStatus": False,
            "clockTime": 0
        })

    pois = []
    pace_list = []
    step_list = []

    total_dist = 0.0
    total_time_s = 0.0
    total_steps = 0
    curr_time_ms = start_timestamp_ms

    last_pace_dist = 0.0
    last_pace_time = 0.0
    last_pace_step = 0
    pace_idx = 1

    last_step_time = 0.0
    last_step_count = 0
    step_idx = 1

    poi_index = random.randint(150, 300)

    while total_dist < target_distance_m:
        target_goal = route_goals[min(current_goal_idx, len(route_goals) - 1)]
        step_dist = speed_mps * sample_interval_s * random.uniform(0.96, 1.04)

        next_lng, next_lat, moved_dist = move_towards(
            curr_lng, curr_lat, target_goal["lng"], target_goal["lat"], step_dist
        )

        # 桩点打卡检测
        dist_to_goal = haversine_distance(next_lat, next_lng, target_goal["lat"], target_goal["lng"])
        if dist_to_goal < 12.0:
            if target_goal.get("code") and target_goal["code"] != "CRUISE":
                for pt in passed_target_points:
                    if pt["code"] == target_goal["code"] and not pt["passStatus"]:
                        pt["passStatus"] = True
                        pt["clockTime"] = curr_time_ms
                        break
            if current_goal_idx < len(route_goals) - 1:
                current_goal_idx += 1
            else:
                route_goals[current_goal_idx] = {
                    "lng": center_lng + random.uniform(-0.0006, 0.0006),
                    "lat": center_lat + random.uniform(-0.0006, 0.0006),
                    "code": "CRUISE"
                }

        # 围栏边界保护
        if not is_point_in_polygon(next_lng, next_lat, poly):
            next_lng = center_lng + (curr_lng - center_lng) * 0.9
            next_lat = center_lat + (curr_lat - center_lat) * 0.9

        # GPS 拟真微漂移
        jitter_lng = random.gauss(0, 0.000002)
        jitter_lat = random.gauss(0, 0.000002)
        p_lng = round(next_lng + jitter_lng, 6)
        p_lat = round(next_lat + jitter_lat, 6)

        actual_moved = haversine_distance(curr_lat, curr_lng, next_lat, next_lng)
        total_dist += actual_moved
        total_time_s += sample_interval_s
        curr_time_ms += int(sample_interval_s * 1000)

        current_cadence = random.gauss(base_cadence_spm, 3.5)
        step_increment = int(round(sample_interval_s * (current_cadence / 60.0)))
        total_steps += step_increment

        satellites_num = random.choice([7, 8, 9, 10, 11, 11, 12])
        accuracy_val = random.choice([1.0, 1.0, 1.0, 0.8, 1.2])
        pois.append({
            "lng": p_lng,
            "lat": p_lat,
            "index": poi_index,
            "collectTime": str(curr_time_ms),
            "createTime": curr_time_ms + 10,
            "runTime": int(total_time_s),
            "satellites": satellites_num,
            "accuracy": accuracy_val,
            "state": 1,
            "offFenceDisM": 0
        })

        curr_lng, curr_lat = next_lng, next_lat
        poi_index += 1

        # 1000 米配速切片
        if (total_dist - last_pace_dist >= 1000.0) or (total_dist >= target_distance_m):
            seg_dist = int(round(total_dist - last_pace_dist))
            seg_time = int(round(total_time_s - last_pace_time))
            seg_steps = total_steps - last_pace_step
            pace_list.append({
                "index": pace_idx,
                "distance": seg_dist,
                "startDistance": int(round(last_pace_dist)),
                "endDistance": int(round(total_dist)),
                "time": seg_time,
                "startTime": int(round(last_pace_time)),
                "endTime": int(round(total_time_s)),
                "stepCount": seg_steps,
                "startStepCount": last_pace_step,
                "endStepCount": total_steps,
                "isValid": True
            })
            pace_idx += 1
            last_pace_dist = total_dist
            last_pace_time = total_time_s
            last_pace_step = total_steps

        # 60 秒步频切片
        if (total_time_s - last_step_time >= 60.0) or (total_dist >= target_distance_m):
            seg_time = int(round(total_time_s - last_step_time))
            seg_steps = total_steps - last_step_count
            step_list.append({
                "index": step_idx,
                "time": seg_time,
                "startTime": int(round(last_step_time)),
                "endTime": int(round(total_time_s)),
                "step": seg_steps,
                "startStep": last_step_count,
                "endStep": total_steps,
                "isValid": True
            })
            step_idx += 1
            last_step_time = total_time_s
            last_step_count = total_steps

    # 兜底确保所有打卡桩已标记
    for idx, pt in enumerate(passed_target_points):
        if not pt["passStatus"] or pt["clockTime"] == 0:
            pt["passStatus"] = True
            pt["clockTime"] = start_timestamp_ms + int(total_time_s * 400 * (idx + 1) / max(1, len(passed_target_points)))

    return {
        "distance": int(round(total_dist)),
        "duration": int(round(total_time_s)),
        "total_step": total_steps,
        "pois": pois,
        "target_points": passed_target_points,
        "pace_list": pace_list,
        "step_list": step_list,
        "start_time_ms": start_timestamp_ms,
        "end_time_ms": curr_time_ms
    }
