import logging
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger("latency")

MAX_HISTORY = 100


@dataclass
class LatencyRecord:
    timestamp: float
    end_to_end_ms: float
    event_type: str


class LatencyTracker:
    def __init__(self) -> None:
        self._history: deque[LatencyRecord] = deque(maxlen=MAX_HISTORY)
        self._pending_start: float | None = None

    def mark_user_speech_end(self) -> None:
        self._pending_start = time.perf_counter()

    def mark_agent_speech_start(self) -> None:
        if self._pending_start is None:
            return
        elapsed_ms = (time.perf_counter() - self._pending_start) * 1000
        record = LatencyRecord(
            timestamp=time.time(),
            end_to_end_ms=round(elapsed_ms, 1),
            event_type="turn_response",
        )
        self._history.append(record)
        logger.info(f"Response latency: {record.end_to_end_ms}ms")
        self._pending_start = None

    def get_summary(self) -> dict:
        if not self._history:
            return {"count": 0, "avg_ms": 0, "min_ms": 0, "max_ms": 0, "recent": []}

        values = [r.end_to_end_ms for r in self._history]
        recent = [
            {
                "timestamp": r.timestamp,
                "end_to_end_ms": r.end_to_end_ms,
                "event_type": r.event_type,
            }
            for r in list(self._history)[-10:]
        ]
        return {
            "count": len(values),
            "avg_ms": round(sum(values) / len(values), 1),
            "min_ms": min(values),
            "max_ms": max(values),
            "recent": recent,
        }


tracker = LatencyTracker()
