"""Local model configuration and session-bound question storage for Easel."""
from __future__ import annotations
import json, os, secrets, threading
from pathlib import Path
from typing import Any
STATE = Path(os.environ.get("EASEL_STATE_DIR", Path.home() / ".easel"))
_questions: dict[str, dict[str, Any]] = {}
_lock = threading.RLock()
def config_path() -> Path: return STATE / "providers.json"
def load_config() -> dict[str, Any]:
    try:
        value = json.loads(config_path().read_text(encoding="utf-8"))
        if isinstance(value, dict) and isinstance(value.get("providers", {}), dict): return value
    except (OSError, ValueError): pass
    return {"primary": "openai", "providers": {}}
def save_config(data: dict[str, Any]) -> None:
    path = config_path(); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(".tmp"); tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600); tmp.replace(path)
def masked(key: str) -> str: return "••••••" + key[-4:] if key else ""
def create_question(session_id: str, questions: list[dict[str, Any]]) -> dict[str, Any]:
    if not questions or len(questions) > 3: raise ValueError("a question card must contain 1–3 questions")
    qid = "easel_" + secrets.token_urlsafe(18); items = []
    for item in questions:
        item_id = str(item.get("questionId") or "q_" + secrets.token_urlsafe(8)); options = item.get("options", [])
        if not isinstance(options, list) or len(options) > 20: raise ValueError("invalid question options")
        items.append({"questionId": item_id, "header": str(item.get("header", ""))[:100], "question": str(item.get("question", ""))[:1000], "options": options, "multiSelect": bool(item.get("multiSelect", False))})
    record = {"id": qid, "sessionId": session_id, "questions": items, "status": "pending", "answers": {}}
    with _lock: _questions[qid] = record
    return record
def answer_question(session_id: str, question_id: str, answers: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        q = _questions.get(question_id)
        if not q or q["sessionId"] != session_id: return {"ok": False, "error": "question not found"}
        if q["status"] != "pending": return {"ok": False, "error": "question already resolved"}
        normalized: dict[str, list[str]] = {}
        for item in q["questions"]:
            key = item["questionId"]; values = answers.get(key)
            if isinstance(values, str): values = [values]
            if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values): return {"ok": False, "error": "every question requires an answer"}
            allowed = {str(opt.get("label", "")) for opt in item["options"] if isinstance(opt, dict)}
            # Free-form "Other" answers are supported by the existing card UI.
            if any(len(v) > 1000 for v in values): return {"ok": False, "error": "answer is too long"}
            if not item["multiSelect"] and len(values) != 1: return {"ok": False, "error": "question accepts one answer"}
            normalized[key] = values
        q["answers"] = normalized; q["status"] = "resolved"
        return {"ok": True, "result": {"status": "resolved"}}
def question_status(session_id: str, ids: list[str]) -> dict[str, dict[str, str]]:
    with _lock: return {qid: {"status": (_questions[qid]["status"] if qid in _questions and _questions[qid]["sessionId"] == session_id else "not_found")} for qid in ids}


def get_question(session_id: str, question_id: str) -> dict[str, Any] | None:
    with _lock:
        record = _questions.get(question_id)
        return record if record and record["sessionId"] == session_id else None
