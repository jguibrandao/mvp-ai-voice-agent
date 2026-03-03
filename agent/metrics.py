import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("latency")

METRICS_FILE = Path(__file__).resolve().parent.parent / "metrics_data.json"
MAX_HISTORY = 100


def _load_history() -> list[dict]:
    try:
        data = json.loads(METRICS_FILE.read_text())
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_history(history: list[dict]) -> None:
    trimmed = history[-MAX_HISTORY:]
    METRICS_FILE.write_text(json.dumps(trimmed, indent=2))


def _safe_log(msg: str) -> None:
    try:
        logger.info(msg)
    except UnicodeEncodeError:
        pass


def _summarize_field(history: list[dict], field: str) -> dict:
    values = [r[field] for r in history if field in r and r[field] is not None]
    if not values:
        return {"avg": 0, "min": 0, "max": 0}
    return {
        "avg": round(sum(values) / len(values), 1),
        "min": min(values),
        "max": max(values),
    }


class LatencyTracker:
    def __init__(self) -> None:
        self._user_speech_end: float | None = None
        self._thinking_start: float | None = None

    def mark_user_speech_end(self) -> None:
        self._user_speech_end = time.perf_counter()
        self._thinking_start = None

    def mark_agent_thinking_start(self) -> None:
        if self._user_speech_end is None:
            return
        self._thinking_start = time.perf_counter()
        ttft_ms = (self._thinking_start - self._user_speech_end) * 1000
        _safe_log(f"TTFT: {ttft_ms:.1f}ms")

    def mark_agent_speech_start(self) -> None:
        if self._user_speech_end is None:
            return
        now = time.perf_counter()
        e2e_ms = (now - self._user_speech_end) * 1000

        ttft_ms = None
        processing_ms = None
        if self._thinking_start is not None:
            ttft_ms = round((self._thinking_start - self._user_speech_end) * 1000, 1)
            processing_ms = round((now - self._thinking_start) * 1000, 1)

        record = {
            "timestamp": time.time(),
            "ttft_ms": ttft_ms,
            "processing_ms": processing_ms,
            "end_to_end_ms": round(e2e_ms, 1),
        }
        history = _load_history()
        history.append(record)
        _save_history(history)

        parts = [f"E2E: {record['end_to_end_ms']}ms"]
        if ttft_ms is not None:
            parts.append(f"TTFT: {ttft_ms}ms")
        if processing_ms is not None:
            parts.append(f"LLM+TTS: {processing_ms}ms")
        _safe_log(" | ".join(parts))

        self._user_speech_end = None
        self._thinking_start = None

    @staticmethod
    def get_summary() -> dict:
        history = _load_history()
        if not history:
            return {
                "count": 0,
                "ttft": {"avg": 0, "min": 0, "max": 0},
                "processing": {"avg": 0, "min": 0, "max": 0},
                "end_to_end": {"avg": 0, "min": 0, "max": 0},
                "recent": [],
            }

        return {
            "count": len(history),
            "ttft": _summarize_field(history, "ttft_ms"),
            "processing": _summarize_field(history, "processing_ms"),
            "end_to_end": _summarize_field(history, "end_to_end_ms"),
            "recent": history[-10:],
        }

    @staticmethod
    def clear() -> None:
        _save_history([])


tracker = LatencyTracker()
