"""
闪动校园 8.7.2 — 核心业务统一门面客户端 (ShanDongClient)
统筹所有业务接口、网络传输、加解密与会话持久化。
"""

import base64
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Callable

import requests

import crypto
import captcha_solver
import session_store
from transport import HttpTransport
from running_protocol import generate_natural_sunrun_trajectory


class ShanDongClient:
    def __init__(
        self,
        token: Optional[str] = None,
        satoken: Optional[str] = None,
        user_id: Optional[str] = None,
        school_code: Optional[str] = None,
        transport_mode: str = "direct",
        proxy: Optional[str] = None,
        adb_path: Optional[str] = None,
        device_id: Optional[str] = None,
        model_name: Optional[str] = None,
        system_version: Optional[str] = None
    ):
        self.transport = HttpTransport(
            token=token,
            satoken=satoken,
            device_id=device_id,
            model_name=model_name,
            system_version=system_version,
            transport_mode=transport_mode,
            proxy=proxy,
            adb_path=adb_path
        )
        self.user_id = user_id
        self.school_code = school_code
        self.user_name = None

        if not self.transport.token:
            self._load_saved_session()

    def _load_saved_session(self) -> None:
        """从本地 session.json 加载会话"""
        s = session_store.load_session()
        if s:
            self.transport.token = s.get("token") or ""
            self.transport.satoken = s.get("satoken") or ""
            self.user_id = s.get("userId")
            self.school_code = s.get("schoolCode")
            self.user_name = s.get("userName")
            if s.get("deviceId"):
                self.transport.device_id = s["deviceId"]

    def _save_current_session(self) -> None:
        """保存当前会话至本地 session.json"""
        s = {
            "token": self.transport.token,
            "satoken": self.transport.satoken,
            "userId": self.user_id,
            "schoolCode": self.school_code,
            "userName": self.user_name,
            "deviceId": self.transport.device_id
        }
        session_store.save_session(s)

    # ==========================================
    # 一、登录鉴权与验证码
    # ==========================================
    def login_check(self, phone: str) -> Dict[str, Any]:
        """登录前手机号状态检查"""
        payload = self.transport.build_base_payload({"loginName": phone})
        return self.transport.post("auth/loginCheck", payload, v_param="loginCheck", api_module="auth")

    def get_captcha(self) -> Dict[str, Any]:
        """获取 AJ-Captcha 滑块拼图图片"""
        payload = {"captchaType": "blockPuzzle"}
        headers = {
            "Host": "api.huachenjie.com",
            "Content-Type": "application/json; charset=utf-8",
            "Origin": "https://mh5.huachenjie.com",
            "Referer": "https://mh5.huachenjie.com/",
            "User-Agent": f"ShanDong/{self.transport.app_version} (Android {self.transport.system_version})",
        }
        url = f"{self.transport.base_url}/captcha/get"
        try:
            resp = self.transport.session.post(url, json=payload, headers=headers, timeout=self.transport.timeout)
            return resp.json()
        except Exception as e:
            return {"code": -1, "message": f"获取验证码失败: {str(e)}"}

    def check_captcha(self, captcha_token: str, raw_x: float) -> Tuple[Dict[str, Any], str]:
        """校验滑块拼图位移"""
        enc_point = crypto.encrypt_slider_point(raw_x)
        payload = {
            "captchaType": "blockPuzzle",
            "pointJson": enc_point,
            "token": captcha_token
        }
        headers = {
            "Host": "api.huachenjie.com",
            "Content-Type": "application/json; charset=utf-8",
            "Origin": "https://mh5.huachenjie.com",
            "Referer": "https://mh5.huachenjie.com/",
            "User-Agent": f"ShanDong/{self.transport.app_version} (Android {self.transport.system_version})",
        }
        url = f"{self.transport.base_url}/captcha/check"
        try:
            resp = self.transport.session.post(url, json=payload, headers=headers, timeout=self.transport.timeout)
            return resp.json(), enc_point
        except Exception as e:
            return {"code": -1, "message": f"校验验证码异常: {str(e)}"}, enc_point

    def login(self, phone: str, password_plain: str) -> Dict[str, Any]:
        """端到端登录流程 (预检 -> 自动解滑块 -> 密文鉴权 -> 持久化)"""
        # 1. 预检
        self.login_check(phone)

        # 2. 获取滑块图片
        c_res = self.get_captcha()
        if c_res.get("code") != 0 or not c_res.get("data"):
            return {"code": -1, "message": f"获取滑块验证码失败: {c_res.get('message')}"}

        c_data = c_res["data"]
        c_token = c_data.get("token")
        bg_b64 = c_data.get("originalImageBase64")
        tmpl_b64 = c_data.get("jigsawImageBase64")

        # 3. 计算位移量
        x_offset = 120.0
        if bg_b64 and tmpl_b64:
            try:
                bg_bytes = base64.b64decode(bg_b64)
                tmpl_bytes = base64.b64decode(tmpl_b64)
                x_offset = captcha_solver.solve_slider_notch(bg_bytes, tmpl_bytes)
            except Exception:
                x_offset = 120.0

        # 4. 校验滑块
        chk_res, enc_pt = self.check_captcha(c_token, x_offset)
        if chk_res.get("code") != 0 or chk_res.get("data", {}).get("result") is not True:
            # 重试一次默认位移
            chk_res, enc_pt = self.check_captcha(c_token, 115.0)

        # 5. 提交密码登录
        enc_pwd = crypto.encrypt_password(password_plain)
        payload = self.transport.build_base_payload({
            "loginName": phone,
            "password": enc_pwd,
            "captchaPoint": enc_pt
        })

        login_res = self.transport.post("auth/loginPassword", payload, v_param="loginPassword", api_module="auth")
        if login_res.get("code") == 0 and "data" in login_res:
            d = login_res["data"]
            self.transport.token = d.get("token", "")
            self.transport.satoken = d.get("satoken", "")
            self.user_id = str(d.get("userId", ""))
            self.school_code = str(d.get("schoolCode", ""))
            self.user_name = d.get("userName")
            self._save_current_session()
            return {"code": 0, "message": "登录成功", "data": d}

        return {"code": login_res.get("code", -1), "message": login_res.get("message", "登录失败"), "raw": login_res}

    # ==========================================
    # 二、用户信息与学校
    # ==========================================
    def get_user_info(self) -> Dict[str, Any]:
        """查询用户基本个人信息"""
        payload = self.transport.build_base_payload()
        return self.transport.post("account/queryCommonUserInfo", payload)

    def get_school_details(self) -> Dict[str, Any]:
        """查询所属学校详情"""
        payload = self.transport.build_base_payload()
        return self.transport.post("api/school/details", payload)

    def get_credit_notes(self) -> Dict[str, Any]:
        """查询诚信学分积分记录"""
        payload = self.transport.build_base_payload()
        return self.transport.post("creditBook/notes", payload)

    def get_semesters(self) -> Dict[str, Any]:
        """查询学期列表"""
        payload = self.transport.build_base_payload()
        return self.transport.post("attend/semesterSelector", payload)

    # ==========================================
    # 三、跑步规则与校园围栏
    # ==========================================
    def get_run_plans(self, semester_code: str = "") -> List[Dict[str, Any]]:
        """获取学期跑步计划列表"""
        payload = self.transport.build_base_payload({"semesterCode": semester_code})
        res = self.transport.post("run/plan/selectList", payload, v_param="plan", api_module="run")
        if res.get("code") == 0:
            return res.get("data", {}).get("list", [])
        return []

    def get_school_fences(self, school_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """查询学校电子围栏与必经打卡桩"""
        code = school_code or self.school_code or ""
        payload = self.transport.build_base_payload({"schoolCode": code})
        res = self.transport.post("school/querySchoolFences", payload, v_param="querySchoolFences", api_module="school")
        if res.get("code") == 0:
            fences = res.get("data", [])
            for f in fences:
                if f.get("schoolName"):
                    f["schoolName"] = crypto.decrypt_field(f["schoolName"])
            return fences
        return []

    def filter_usable_fence(self, fence_code: str) -> Dict[str, Any]:
        """筛选可用围栏有效性"""
        payload = self.transport.build_base_payload({"fenceCodeList": [str(fence_code)]})
        return self.transport.post("school/filterUsableFence", payload)

    def query_sunrun_rule(self, run_plan_code: str = "", semester_code: str = "") -> Dict[str, Any]:
        """查询阳光跑各项指标考核规则 (配速、单次里程、单日上限、学期总量)"""
        payload = self.transport.build_base_payload({
            "runPlanCode": run_plan_code,
            "semesterCode": semester_code,
            "sportType": "1"
        })
        return self.transport.post("run/querySunRunAbstractInfoV2", payload, v_param="querySunRunAbstractInfoV2", api_module="run")

    def check_sunrun_config(self, fence_code: str, target_distance: str = "2000", sub_school_code: str = "") -> Dict[str, Any]:
        """检查阳光跑配置 (包含人脸策略、NFC状态与起跑 Ticket)"""
        payload = self.transport.build_base_payload({
            "runPlanCode": "",
            "schoolCode": self.school_code or "",
            "subSchoolCode": sub_school_code,
            "fenceCode": fence_code,
            "sportType": "1",
            "targetDistance": str(target_distance)
        })
        return self.transport.post("run/checkSunRunConfig", payload, v_param="checkSunRunConfig", api_module="run")

    # ==========================================
    # 四、跑步记录与统计
    # ==========================================
    def get_run_summary(self, sport_type: int = 2, time_type: int = 3) -> Dict[str, Any]:
        """查询累计跑步统计 (总里程/总用时/总卡路里/达标天数)"""
        payload = self.transport.build_base_payload({
            "sportType": str(sport_type),
            "timeType": str(time_type)
        })
        return self.transport.post("run/queryRunRecordCount", payload)

    def get_sun_run_records(self, page_num: int = 1, page_size: int = 10, semester_code: str = "") -> Dict[str, Any]:
        """分页查询阳光跑打卡记录"""
        payload = self.transport.build_base_payload({
            "pageNum": str(page_num),
            "pageSize": str(page_size),
            "semesterCode": semester_code,
            "runPlanCode": ""
        })
        return self.transport.post("run/pageSunRunRecord", payload)

    def get_free_run_records(self, page_num: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """分页查询自由跑打卡记录"""
        payload = self.transport.build_base_payload({
            "pageNum": page_num,
            "pageSize": page_size,
            "timeType": 3
        })
        return self.transport.post("run/pageFreeRunRecordList", payload)

    # ==========================================
    # 五、校园排行榜
    # ==========================================
    def get_distance_rank(self, rank_cycle: int = 30, sex: int = 2) -> Dict[str, Any]:
        """查询 30 天全校里程排行榜"""
        payload = self.transport.build_base_payload({
            "rankCycle": str(rank_cycle),
            "sex": str(sex),
            "type": "1",
            "scope": "50",
            "runPlanCode": ""
        })
        return self.transport.post("rank/distance", payload)

    def get_progress_rank(self, sex: int = 2) -> Dict[str, Any]:
        """查询全校达标进度排行榜"""
        payload = self.transport.build_base_payload({
            "sex": str(sex),
            "scope": "50",
            "runPlanCode": ""
        })
        return self.transport.post("rank/runProgress", payload)

    # ==========================================
    # 六、室外跑步打卡 (自由跑 / 阳光跑)
    # ==========================================
    def clean_unfinished_run(self, sport_type: int = 2) -> Optional[str]:
        """清理未结束的残留跑步会话"""
        payload = self.transport.build_base_payload({"sportType": str(sport_type)})
        res = self.transport.post("run/queryUnFinishRun", payload, v_param="queryUnFinishRun", api_module="run")
        if res.get("code") == 0 and res.get("data", {}).get("runRecordCode"):
            code = res["data"]["runRecordCode"]
            curr_ts = str(int(time.time() * 1000))
            self.transport.post("run/finishFreeRun", self.transport.build_base_payload({
                "runRecordCode": code, "distance": "0", "duration": "0", "totalStep": "0",
                "timestamp": curr_ts
            }))
            return code
        return None

    def submit_free_run(
        self,
        distance_m: int = 3010,
        avg_pace_sec: int = 358,
        aim_distance: Optional[int] = None,
        fence_index: int = 0
    ) -> Dict[str, Any]:
        """
        执行自由跑打卡：
        - 自动获取校园围栏
        - 生成高拟真 360 点轨迹与分钟级步频曲线
        - 分批上报轨迹切片
        - 结算提交
        """
        fences = self.get_school_fences()
        chosen_fence = fences[min(fence_index, len(fences) - 1)] if fences else {}
        fence_list = chosen_fence.get("fenceList", [])
        start_lat = chosen_fence.get("lat")
        start_lng = chosen_fence.get("lng")
        if (start_lat is None or start_lng is None) and fence_list:
            start_lat = fence_list[0].get("lat")
            start_lng = fence_list[0].get("lng")

        if start_lat is None or start_lng is None:
            return {"code": -1, "message": "无法从当前学校配置获取有效电子围栏或起跑经纬度"}

        start_lat = str(start_lat)
        start_lng = str(start_lng)

        self.clean_unfinished_run(sport_type=2)

        # 1. 申请开始起跑
        start_payload = {"lat": start_lat, "lng": start_lng}
        if aim_distance is not None and aim_distance > 0:
            start_payload["aimDistance"] = str(int(aim_distance))

        start_res = self.transport.post(
            "run/startFreeRun",
            self.transport.build_base_payload(start_payload),
            v_param="startFreeRun",
            api_module="run"
        )
        if start_res.get("code") != 0 or not start_res.get("data", {}).get("runRecordCode"):
            return {"code": -1, "message": f"起跑申请失败: {start_res.get('message')}"}

        run_record_code = start_res["data"]["runRecordCode"]

        # 2. 生成高拟真轨迹
        now_ms = int(time.time() * 1000)
        actual_distance = (aim_distance + 20) if (aim_distance and aim_distance > 0) else distance_m
        expected_duration = int(actual_distance / (1000.0 / avg_pace_sec))
        start_ms = now_ms - (expected_duration * 1000)

        traj = generate_natural_sunrun_trajectory(
            fence_boundary=fence_list,
            target_points=[],
            target_distance_m=actual_distance,
            avg_pace_sec_per_km=avg_pace_sec,
            start_timestamp_ms=start_ms
        )

        # 3. 分批上报轨迹点 (每批 50 点)
        all_pois = traj["pois"]
        batch_size = 50
        for i in range(0, len(all_pois), batch_size):
            chunk = all_pois[i:i + batch_size]
            self.transport.post("run/uploadRunRecord", self.transport.build_base_payload({
                "runRecordCode": run_record_code,
                "pois": chunk
            }), v_param="uploadRunRecord", api_module="run")

        # 4. 提交结算
        curr_ts = str(now_ms)
        finish_data = {
            "runRecordCode": run_record_code,
            "distance": str(traj["distance"]),
            "duration": str(traj["duration"]),
            "totalStep": str(traj["total_step"]),
            "paceInterval": 1000,
            "stepInterval": 60,
            "pois": all_pois[-4:] if len(all_pois) >= 4 else all_pois,
            "paceList": traj["pace_list"],
            "stepList": traj["step_list"],
            "timestamp": curr_ts
        }
        if aim_distance is not None and aim_distance > 0:
            finish_data["status"] = 2

        finish_res = self.transport.post("run/finishFreeRun", self.transport.build_base_payload(finish_data))
        if finish_res.get("code") == 0:
            return {
                "code": 0,
                "message": "打卡成功",
                "data": {
                    "runRecordCode": run_record_code,
                    "distance": traj["distance"],
                    "duration": traj["duration"],
                    "steps": traj["total_step"],
                    "poisCount": len(all_pois)
                }
            }
        return {"code": finish_res.get("code", -1), "message": finish_res.get("message", "结算失败"), "raw": finish_res}

    def submit_sun_run(
        self,
        distance_m: int = 3010,
        avg_pace_sec: int = 358,
        fence_index: int = 0,
        mode: str = "second_fresh",
        interval_sec: float = 3.0,
        callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        执行阳光跑打卡：
        - 拉取计划与围栏
        - 起跑获取必经打卡桩 (targetPoints)
        - 倒推起点时间，生成 100% 途经桩点的高拟真传感器轨迹
        - 分批上报轨迹切片与打卡桩通过状态
        - 动态计算防篡改校验码 runImgRecord 提交结算
        """
        # 1. 计划与围栏
        plans = self.get_run_plans()
        plan_code = plans[0].get("runPlanCode") if plans else ""

        fences = self.get_school_fences()
        if not fences:
            return {"code": -1, "message": "获取校园围栏失败"}

        chosen_fence = fences[min(fence_index, len(fences) - 1)]
        fence_code = chosen_fence.get("fenceCode")
        fence_list = chosen_fence.get("fenceList", [])
        sub_school_code = chosen_fence.get("subSchoolCode", "")

        # 2. 预检
        self.filter_usable_fence(fence_code)
        cfg_res = self.check_sunrun_config(fence_code, str(distance_m), sub_school_code)
        if cfg_res.get("code") != 0:
            return {"code": -1, "message": f"起跑配置检查未通过: {cfg_res.get('message')}"}

        face_img = cfg_res.get("data", {}).get("faceImg", "")

        # 3. 申请起跑
        start_payload = {
            "runPlanCode": plan_code,
            "schoolCode": self.school_code or "",
            "fenceCode": fence_code,
            "lng": str(chosen_fence.get("lng")),
            "lat": str(chosen_fence.get("lat")),
            "sportType": "1",
            "targetDistance": str(distance_m),
            "useCreditSword": "false"
        }
        start_res = self.transport.post(
            "run/startSunRun_v2",
            self.transport.build_base_payload(start_payload),
            v_param="startSunRun_v2",
            api_module="run"
        )
        if start_res.get("code") != 0 or not start_res.get("data", {}).get("runRecordCode"):
            return {"code": -1, "message": f"阳光跑起跑申请失败: {start_res.get('message')}"}

        data = start_res["data"]
        run_record_code = data.get("runRecordCode")
        target_points = data.get("targetPoints", [])

        # 4. 生成轨迹
        now_ms = int(time.time() * 1000)
        expected_duration = int(distance_m / (1000.0 / avg_pace_sec))
        start_ms = now_ms - (expected_duration * 1000) if mode == "second_fresh" else now_ms

        traj = generate_natural_sunrun_trajectory(
            fence_boundary=fence_list,
            target_points=target_points,
            target_distance_m=distance_m,
            avg_pace_sec_per_km=avg_pace_sec,
            start_timestamp_ms=start_ms
        )

        all_pois = traj["pois"]

        if mode == "heartbeat":
            # 真实挂机心跳模式
            if callback:
                callback(f"心跳挂机已启动，预计运行 {traj['duration']} 秒，点数: {len(all_pois)}")
            pending_pois = []
            for idx, p in enumerate(all_pois):
                time.sleep(interval_sec)
                p["collectTime"] = str(int(time.time() * 1000))
                pending_pois.append(p)
                if len(pending_pois) >= 5:
                    self.transport.post("run/uploadRunRecord", self.transport.build_base_payload({
                        "runRecordCode": run_record_code,
                        "pois": pending_pois
                    }), v_param="uploadRunRecord", api_module="run")
                    pending_pois = []
                    if callback:
                        callback(f"心跳步进: 已完成 {idx+1}/{len(all_pois)} 点")
            if pending_pois:
                self.transport.post("run/uploadRunRecord", self.transport.build_base_payload({
                    "runRecordCode": run_record_code,
                    "pois": pending_pois
                }), v_param="uploadRunRecord", api_module="run")
        else:
            # 秒刷模式：分批快速灌入轨迹点
            batch_size = 50
            for i in range(0, len(all_pois), batch_size):
                chunk = all_pois[i:i + batch_size]
                self.transport.post("run/uploadRunRecord", self.transport.build_base_payload({
                    "runRecordCode": run_record_code,
                    "pois": chunk
                }), v_param="uploadRunRecord", api_module="run")

        # 5. 上报打卡桩通过状态
        pass_pts = []
        for tp in traj["target_points"]:
            pass_pts.append({
                "code": tp["code"],
                "lng": float(tp["lng"]),
                "lat": float(tp["lat"]),
                "passStatus": True,
                "clockTime": tp.get("clockTime", now_ms)
            })
        self.transport.post("run/uploadPassPoint", self.transport.build_base_payload({
            "runRecordCode": run_record_code,
            "targetPoints": pass_pts
        }), v_param="uploadPassPoint", api_module="run")

        # 6. 计算防篡改结算码与人脸数据
        curr_ts = str(int(time.time() * 1000))
        run_img_record = crypto.calculate_run_img_record(
            run_record_code=run_record_code,
            timestamp_str=curr_ts,
            build_version=self.transport.build_version,
            app_version=self.transport.app_version
        )

        face_list = []
        if face_img and target_points:
            face_list = [{
                "checkDistance": 1200,
                "randomDistance": 1205,
                "runFaceImg": face_img,
                "checkLng": traj["target_points"][0]["lng"],
                "checkLat": traj["target_points"][0]["lat"],
                "confidence": 92.5,
                "checkIndex": 1,
                "runFaceUpload": True,
                "popTime": start_ms + 400000,
                "hasChecked": True,
                "finishFaceCheck": True,
                "rate": 1.0,
                "stability": 0,
                "extendParam": json.dumps({"baseImageDownload": 1, "similarityCheck": 1, "uploadImage": 1})
            }]

        finish_payload = {
            "runRecordCode": run_record_code,
            "distance": str(int(traj["distance"])),
            "duration": str(int(traj["duration"])),
            "totalStep": str(int(traj["total_step"])),
            "sportType": 1,
            "stepInterval": 60,
            "paceInterval": 1000,
            "pauseCount": 0,
            "pauseTimes": 0,
            "alignType": 3,
            "status": 1,
            "runImgRecord": run_img_record,
            "targetPoints": traj["target_points"],
            "pois": all_pois[-4:] if len(all_pois) >= 4 else all_pois,
            "stepList": traj["step_list"],
            "paceList": traj["pace_list"],
            "timestamp": curr_ts,
            "faceCheckRecordList": face_list
        }

        finish_res = self.transport.post("run/finishSunRun_v2", self.transport.build_base_payload(finish_payload))
        if finish_res.get("code") == 0:
            return {
                "code": 0,
                "message": "阳光跑打卡成功",
                "data": {
                    "runRecordCode": run_record_code,
                    "distance": traj["distance"],
                    "duration": traj["duration"],
                    "steps": traj["total_step"],
                    "poisCount": len(all_pois)
                }
            }
        return {"code": finish_res.get("code", -1), "message": finish_res.get("message", "结算失败"), "raw": finish_res}

    # ==========================================
    # 七、室内 AI 运动
    # ==========================================
    def get_ai_categories(self) -> Dict[str, Any]:
        """获取 AI 运动分类列表"""
        payload = self.transport.build_base_payload()
        return self.transport.post("ai/getAICategory", payload, v_param="getAICategory", api_module="ai")

    def get_indoor_config(self, sport_type: int = 1) -> Dict[str, Any]:
        """获取指定 AI 运动配置要求 (如 requireTime 等)"""
        payload = self.transport.build_base_payload({"type": sport_type})
        return self.transport.post("indoor/config", payload, v_param="config", api_module="indoor")

    def get_indoor_sport_count(self, sport_type: int = 1) -> Dict[str, Any]:
        """查询 AI 运动累计数据"""
        payload = self.transport.build_base_payload({"type": sport_type})
        return self.transport.post("indoor/sportCount", payload, v_param="sportCount", api_module="indoor")

    def get_indoor_sports_page(self, sport_type: int = 1, page_num: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """分页查询 AI 运动打卡明细"""
        payload = self.transport.build_base_payload({
            "type": sport_type,
            "pageNum": page_num,
            "pageSize": page_size
        })
        return self.transport.post("indoor/sportsPage", payload, v_param="sportsPage", api_module="indoor")

    def submit_indoor_exercise(
        self,
        sport_type: int = 1,
        total_count: int = 30,
        duration: int = 60
    ) -> Dict[str, Any]:
        """完成并结算单次 AI 室内运动"""
        cfg_res = self.get_indoor_config(sport_type)
        require_duration = 60
        if cfg_res.get("code") == 0 and cfg_res.get("data"):
            require_duration = cfg_res["data"].get("requireTime", 60)

        now_ms = int(time.time() * 1000)
        start_ms = now_ms - (duration * 1000)

        payload = self.transport.build_base_payload({
            "type": int(sport_type),
            "startTime": int(start_ms),
            "total": int(total_count),
            "duration": int(duration),
            "requireDuration": int(require_duration)
        })

        res = self.transport.post("indoor/finish", payload, v_param="finish", api_module="indoor")
        if res.get("code") == 0:
            d = res.get("data", {})
            return {
                "code": 0,
                "message": "AI运动结算成功",
                "data": {
                    "sportsRecordCode": d.get("sportsRecordCode"),
                    "energy": d.get("energy"),
                    "calorie": d.get("calorie"),
                    "sportType": sport_type,
                    "total": total_count,
                    "duration": duration
                }
            }
        return {"code": res.get("code", -1), "message": res.get("message", "结算失败"), "raw": res}
