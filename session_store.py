import json
import os
from typing import Dict, Any, Optional

SESSION_FILE = os.path.join(os.path.dirname(__file__), "session.json")

def load_session() -> Dict[str, Any]:
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_session(session_data: Dict[str, Any]) -> None:
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def clear_session() -> None:
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except Exception:
            pass

