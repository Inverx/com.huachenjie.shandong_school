import json
import time
import base64
from typing import Dict, Any, List, Optional
import crypto
import captcha_solver
from transport import HttpTransport
import session_store

class ShanDongClient:
    def __init__(self, use_adb: bool = True):
        self.transport = HttpTransport(use_adb=use_adb)
        self.user_id = None
        self.school_code = None
        self.user_name = None
        self._load_saved_session()

    def _load_saved_session(self):
        s = session_store.load_session()
        if s:
            self.transport.token = s.get("token")
            self.transport.satoken = s.get("satoken")
            self.user_id = s.get("userId")
            self.school_code = s.get("schoolCode")
            self.user_name = s.get("userName")

    def _save_current_session(self):
        s = {
            "token": self.transport.token,
            "satoken": self.transport.satoken,
            "userId": getattr(self, "user_id", None),
            "schoolCode": getattr(self, "school_code", None),
            "userName": getattr(self, "user_name", None)
        }
        session_store.save_session(s)

    # ==========================================
    # 1. 登录与人机验证
    # ==========================================
    def login(self, phone: str, password_plain: str) -> Dict[str, Any]:
        # 1. Get captcha images via H5 endpoint
        b64_get = base64.b64encode(b'{"captchaType":"blockPuzzle"}').decode()
        self.transport._exec_adb_shell(f"echo {b64_get} | base64 -d > /data/local/tmp/req_get.json")
        
        curl_get = f'curl -s -X POST "{self.transport.base_url}/run-front/captcha/get" -H "Content-Type: application/json" -H "Origin: https://mh5.huachenjie.com" -H "Referer: https://mh5.huachenjie.com/" -H "X-Requested-With: com.huachenjie.shandong_school" -H "User-Agent: Mozilla/5.0 (Linux; Android 12; {self.transport.model_name}) Chrome/150.0 shandong/{self.transport.app_version}" --data-binary @/data/local/tmp/req_get.json'
        raw_get = self.transport._exec_adb_shell(curl_get).decode('utf-8', errors='ignore')
        
        try:
            captcha_raw = json.loads(raw_get)
        except Exception:
            return {"error": -1, "message": "解析验证码响应失败", "raw": raw_get}
            
        if captcha_raw.get("code") != 0 or "data" not in captcha_raw:
            return {"error": -1, "message": "获取验证码失败: " + str(captcha_raw.get("message")), "raw": captcha_raw}
            
        c_data = captcha_raw["data"]
        token = c_data["token"]
        bg_url = c_data["originalImageUrl"]
        tmpl_url = c_data["jigsawImageUrl"]
        
        # 2. Download images via phone network concurrently
        self.transport._exec_adb_shell(f'curl -s "{bg_url}" > /data/local/tmp/bg.png & curl -s "{tmpl_url}" > /data/local/tmp/tmpl.png & wait')
        bg_b64 = self.transport._exec_adb_shell("base64 /data/local/tmp/bg.png").strip()
        tmpl_b64 = self.transport._exec_adb_shell("base64 /data/local/tmp/tmpl.png").strip()
        
        # 3. Solve slider using OpenCV
        x_offset = captcha_solver.solve_slider_notch(base64.b64decode(bg_b64), base64.b64decode(tmpl_b64))
        
        # 4. Encrypt pointJson and check
        pt_json = crypto.encrypt_captcha_point(x_offset, 15.0, crypto.KEY_CAPTCHA_POINT)
        
        payload_chk = json.dumps({
            "captchaType": "blockPuzzle",
            "pointJson": pt_json,
            "token": token
        })
        b64_chk = base64.b64encode(payload_chk.encode('utf-8')).decode()
        self.transport._exec_adb_shell(f"echo {b64_chk} | base64 -d > /data/local/tmp/chk.json")
        
        curl_chk = f'curl -s -X POST "{self.transport.base_url}/run-front/captcha/check" -H "Content-Type: application/json" -H "Origin: https://mh5.huachenjie.com" -H "Referer: https://mh5.huachenjie.com/" -H "X-Requested-With: com.huachenjie.shandong_school" -H "User-Agent: Mozilla/5.0 (Linux; Android 12; {self.transport.model_name}) Chrome/150.0 shandong/{self.transport.app_version}" --data-binary @/data/local/tmp/chk.json'
        raw_chk = self.transport._exec_adb_shell(curl_chk).decode('utf-8', errors='ignore')
        
        try:
            chk_res = json.loads(raw_chk)
        except Exception:
            return {"error": -1, "message": "解析验证码校验响应失败", "raw": raw_chk}
            
        if chk_res.get("data", {}).get("result") is not True:
            return {"error": -1, "message": "滑块验证未通过", "raw": chk_res}
            
        # 5. Submit login
        enc_pwd = crypto.encrypt_field(password_plain)
        login_res = self.transport.post("/run-front/auth/loginPassword", {
            "loginName": phone,
            "password": enc_pwd,
            "captchaPoint": pt_json
        }, extra_headers={"app": "run-front", "api": "auth", "v": "loginPassword", "e": "1", "pv": "2", "k": ""})
        
        if login_res.get("code") == 0 and "data" in login_res:
            d = login_res["data"]
            self.transport.token = d.get("token")
            self.transport.satoken = d.get("satoken")
            self.user_id = d.get("userId")
            self.school_code = d.get("schoolCode")
            self._save_current_session()
            return {"error": 0, "message": "登录成功", "data": d}
        else:
            return {"error": login_res.get("code", -1), "message": login_res.get("message", "登录失败"), "raw": login_res}

    # ==========================================
    # 2. 用户与学校规则信息
    # ==========================================
    def get_user_info(self) -> Dict[str, Any]:
        return self.transport.post("/run-front/account/queryCommonUserInfo")

    def get_school_fences(self, school_code: Optional[str] = None) -> Dict[str, Any]:
        code = school_code or getattr(self, "school_code", None) or "学校id"
        res = self.transport.post("/run-front/school/querySchoolFences", {"schoolCode": code}, extra_headers={
            "app": "run-front", "api": "school", "v": "querySchoolFences", "e": "0", "pv": "2", "k": ""
        })
        if res.get("code") == 0 and "data" in res:
            for item in res["data"]:
                if "schoolName" in item and item["schoolName"]:
                    item["schoolName"] = crypto.decrypt_field(item["schoolName"])
        return res

    def get_school_details(self) -> Dict[str, Any]:
        return self.transport.post("/run-front/api/school/details")

    def get_credit_notes(self) -> Dict[str, Any]:
        return self.transport.post("/run-front/creditBook/notes")

    def get_semesters(self) -> Dict[str, Any]:
        return self.transport.post("/run-front/attend/semesterSelector")

    # ==========================================
    # 3. 跑步记录与统计
    # ==========================================
    def get_run_summary(self, sport_type: int = 2, time_type: int = 3) -> Dict[str, Any]:
        return self.transport.post("/run-front/run/queryRunRecordCount", {"sportType": str(sport_type), "timeType": str(time_type)})

    def get_sun_run_records(self, page_num: int = 1, page_size: int = 10, semester_code: str = "") -> Dict[str, Any]:
        return self.transport.post("/run-front/run/pageSunRunRecord", {
            "pageNum": str(page_num), "pageSize": str(page_size), "semesterCode": semester_code, "runPlanCode": ""
        })

    def get_free_run_records(self, page_num: int = 1, page_size: int = 10) -> Dict[str, Any]:
        return self.transport.post("/run-front/run/pageFreeRunRecordList", {
            "pageNum": page_num, "pageSize": page_size, "timeType": 3
        })

    # ==========================================
    # 4. 排行榜
    # ==========================================
    def get_distance_rank(self, rank_cycle: int = 30, sex: int = 2) -> Dict[str, Any]:
        return self.transport.post("/run-front/rank/distance", {
            "rankCycle": str(rank_cycle), "sex": str(sex), "type": "1", "scope": "50", "runPlanCode": ""
        })

    def get_progress_rank(self, sex: int = 2) -> Dict[str, Any]:
        return self.transport.post("/run-front/rank/runProgress", {
            "sex": str(sex), "scope": "50", "runPlanCode": ""
        })

    # ==========================================
    # 5. AI 运动
    # ==========================================
    def get_ai_categories(self) -> Dict[str, Any]:
        return self.transport.post("/run-front/ai/getAICategory")

    def get_ai_records(self, page_num: int = 1, page_size: int = 10) -> Dict[str, Any]:
        return self.transport.post("/run-front/ai/pageRecordList", {
            "pageNum": page_num, "pageSize": page_size, "semesterCode": None, "aiExercisePlanCode": None
        })

    # ==========================================
    # 6. 跑步打卡全流程
    # ==========================================
    def submit_free_run(self, distance_m: int = 2000, avg_pace_sec: int = 320) -> Dict[str, Any]:
        # 1. Get fences
        f_res = self.get_school_fences()
        if f_res.get("code") != 0 or not f_res.get("data"):
            return {"error": -1, "message": "无法获取校园围栏"}
        fence = f_res["data"][1] if len(f_res["data"]) > 1 else f_res["data"][0]
        
        # 2. Build trajectory
        import protocol_builder
        session = protocol_builder.build_run_trajectory(fence["fenceList"], distance_m, avg_pace_sec)
        
        # 3. Start run session
        start_pt = session["pois"][0]
        start_res = self.transport.post("/run-front/run/startFreeRun", {
            "lat": str(start_pt["lat"]), "lng": str(start_pt["lng"])
        }, extra_headers={"app": "run-front", "api": "run", "v": "startFreeRun", "e": "0", "pv": "2", "k": ""})
        
        if start_res.get("code") != 0 or "data" not in start_res:
            return {"error": start_res.get("code", -1), "message": "申请开始跑步失败", "raw": start_res}
        run_record_code = start_res["data"]["runRecordCode"]
        
        # 4. Upload GPS chunks (upload 2 sample chunks)
        all_pois = session["pois"]
        chunk_size = 15
        for i in range(0, min(len(all_pois), 30), chunk_size):
            self.transport.post("/run-front/run/uploadRunRecord", {
                "runRecordCode": run_record_code, "pois": all_pois[i:i+chunk_size]
            })
            
        # 5. Finish free run
        curr_ts = str(int(time.time() * 1000))
        run_img_record = crypto.compute_run_img_record(run_record_code, self.transport.sign_key, curr_ts)
        
        finish_res = self.transport.post("/run-front/run/finishFreeRun", {
            "runRecordCode": run_record_code,
            "distance": str(session["total_distance_m"]),
            "duration": str(session["duration_s"]),
            "totalStep": str(session["total_steps"]),
            "paceInterval": 50,
            "stepInterval": 20,
            "pois": all_pois,
            "paceList": session["pace_list"],
            "stepList": session["step_list"],
            "runImgRecord": run_img_record,
            "timestamp": curr_ts
        })
        
        if finish_res.get("code") == 0:
            return {
                "error": 0,
                "message": "打卡成功",
                "data": {
                    "runRecordCode": run_record_code,
                    "distance": session["total_distance_m"],
                    "duration": session["duration_s"],
                    "steps": session["total_steps"],
                    "reward": finish_res.get("data")
                }
            }
        else:
            return {"error": finish_res.get("code", -1), "message": finish_res.get("message", "打卡结算失败"), "raw": finish_res}

