import math
import random
from typing import List, Dict, Any, Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Earth radius in meters
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2.0) ** 2
    return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def is_point_in_polygon(x: float, y: float, poly: List[Tuple[float, float]]) -> bool:
    # Ray-casting algorithm for Point-in-Polygon (PIP) check
    n = len(poly)
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

def build_run_trajectory(fence_points: List[Dict[str, float]], 
                         target_distance_m: float = 2000.0, 
                         avg_pace_sec_per_km: int = 330) -> Dict[str, Any]:
    # Generates realistic human running trajectory within polygon bounds
    poly = [(p["lng"], p["lat"]) for p in fence_points]
    lngs = [p[0] for p in poly]
    lats = [p[1] for p in poly]
    center_lng = sum(lngs) / len(lngs)
    center_lat = sum(lats) / len(lats)
    
    speed_mps = 1000.0 / avg_pace_sec_per_km
    step_cadence_spm = random.randint(165, 178)
    step_length_m = speed_mps / (step_cadence_spm / 60.0)
    sample_interval_s = 2.5
    step_dist_per_sample = speed_mps * sample_interval_s
    
    curr_lng = center_lng + random.uniform(-0.0004, 0.0004)
    curr_lat = center_lat + random.uniform(-0.0004, 0.0004)
    heading = random.uniform(0, 2 * math.pi)
    
    m_to_lat = 1.0 / 111111.0
    m_to_lng = 1.0 / (111111.0 * math.cos(math.radians(28.13)))
    
    pois = [{"lng": round(curr_lng, 6), "lat": round(curr_lat, 6), "stability": 0}]
    pace_list = []
    step_list = []
    
    total_dist, total_time_s, total_steps = 0.0, 0.0, 0
    last_pace_dist, last_pace_time, last_pace_step, pace_idx = 0.0, 0.0, 0, 0
    last_step_time, last_step_count, step_idx = 0.0, 0, 0
    
    while total_dist < target_distance_m:
        heading += random.uniform(-0.18, 0.18)
        step_m = step_dist_per_sample * random.uniform(0.95, 1.05)
        dlng = step_m * math.sin(heading) * m_to_lng
        dlat = step_m * math.cos(heading) * m_to_lat
        
        next_lng = curr_lng + dlng
        next_lat = curr_lat + dlat
        
        if not is_point_in_polygon(next_lng, next_lat, poly):
            heading = math.atan2(center_lng - curr_lng, center_lat - curr_lat) + random.uniform(-0.3, 0.3)
            dlng = step_m * math.sin(heading) * m_to_lng
            dlat = step_m * math.cos(heading) * m_to_lat
            next_lng = curr_lng + dlng
            next_lat = curr_lat + dlat
            
        jitter_lng = random.gauss(0, 0.3 * m_to_lng)
        jitter_lat = random.gauss(0, 0.3 * m_to_lat)
        p_lng = round(next_lng + jitter_lng, 6)
        p_lat = round(next_lat + jitter_lat, 6)
        
        seg_dist = haversine_distance(curr_lat, curr_lng, next_lat, next_lng)
        total_dist += seg_dist
        total_time_s += sample_interval_s
        seg_steps = int(round(seg_dist / step_length_m))
        total_steps += seg_steps
        
        pois.append({"lng": p_lng, "lat": p_lat, "stability": 0})
        curr_lng, curr_lat = next_lng, next_lat
        
        # 50m Pace segments
        if total_dist - last_pace_dist >= 50.0 or total_dist >= target_distance_m:
            pace_list.append({
                "index": pace_idx,
                "distance": int(round(total_dist - last_pace_dist)),
                "startDistance": int(round(last_pace_dist)),
                "endDistance": int(round(total_dist)),
                "time": int(round(total_time_s - last_pace_time)),
                "startTime": int(round(last_pace_time)),
                "endTime": int(round(total_time_s)),
                "stepCount": total_steps - last_pace_step,
                "startStepCount": last_pace_step,
                "endStepCount": total_steps,
                "stability": 0
            })
            pace_idx += 1
            last_pace_dist = total_dist
            last_pace_time = total_time_s
            last_pace_step = total_steps
            
        # 20s Step segments
        if total_time_s - last_step_time >= 20.0 or total_dist >= target_distance_m:
            step_list.append({
                "index": step_idx,
                "time": int(round(total_time_s - last_step_time)),
                "startTime": int(round(last_step_time)),
                "endTime": int(round(total_time_s)),
                "step": total_steps - last_step_count,
                "startStep": last_step_count,
                "endStep": total_steps,
                "stability": 0
            })
            step_idx += 1
            last_step_time = total_time_s
            last_step_count = total_steps

    return {
        "total_distance_m": int(round(total_dist)),
        "duration_s": int(round(total_time_s)),
        "total_steps": total_steps,
        "pois": pois,
        "pace_list": pace_list,
        "step_list": step_list
    }

