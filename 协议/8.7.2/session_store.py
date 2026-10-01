import json
import os
from typing import Dict, Any, Optional

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session.json")


def load_session() -> Dict[str, Any]:
    """从本地读取保存的会话状态"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_session(session_data: Dict[str, Any]) -> None:
    """保存当前会话状态至本地 session.json"""
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clear_session() -> None:
    """清除本地保存的会话文件"""
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except Exception:
            pass
