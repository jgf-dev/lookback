from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AudioSession:
    session_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    bytes_received: int = 0


class StreamManager:
    def __init__(self) -> None:
        self._sessions: dict[str, AudioSession] = {}
        self._buffers: dict[str, bytearray] = defaultdict(bytearray)

    def start(self, session_id: str) -> AudioSession:
        session = AudioSession(session_id=session_id)
        self._sessions[session_id] = session
        self._buffers[session_id] = bytearray()
        return session

    def append_chunk(self, session_id: str, chunk: bytes) -> int:
        if session_id not in self._sessions:
            self.start(session_id)
        self._buffers[session_id].extend(chunk)
        self._sessions[session_id].bytes_received += len(chunk)
        return len(self._buffers[session_id])

    def consume(self, session_id: str) -> bytes:
        payload = bytes(self._buffers[session_id])
        self._buffers[session_id].clear()
        return payload

    def close(self, session_id: str) -> AudioSession | None:
        self._buffers.pop(session_id, None)
        return self._sessions.pop(session_id, None)
