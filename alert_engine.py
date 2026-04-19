from collections import deque
from dataclasses import dataclass, field
from time import time
import math

@dataclass
class AlertConfig:
    sustained_hr_threshold: int = 110
    sustained_duration_secs: int = 10
    spike_bpm_delta: int = 30
    spike_window_secs: int = 30
    min_window_secs: int = 5

@dataclass
class AlertEvent:
    type: str
    message: str
    bpm: int
    timestamp: float = field(default_factory=time)

class AlertEngine:
    def __init__(self, config=None):
        self.config = config or AlertConfig()
        self._window = deque()
        self._rr_buffer = deque(maxlen=20)
        self._spike_alerted = False
        self._sustained_alerted = False
        self._sustained_start = None

    def update(self, bpm, rr_intervals=None):
        now = time()
        if rr_intervals:
            self._rr_buffer.extend(rr_intervals)
        self._window.append((now, bpm))
        cutoff = now - self.config.spike_window_secs
        while self._window and self._window[0][0] < cutoff:
            self._window.popleft()
        if bpm > self.config.sustained_hr_threshold:
            if self._sustained_start is None:
                self._sustained_start = now
            elapsed = now - self._sustained_start
            if elapsed >= self.config.sustained_duration_secs and not self._sustained_alerted:
                self._sustained_alerted = True
                return AlertEvent(
                    type="sustained",
                    message=f"Heart rate above {self.config.sustained_hr_threshold} BPM for {int(elapsed)} seconds. Please rest.",
                    bpm=bpm,
                )
        else:
            self._sustained_start = None
            self._sustained_alerted = False
        window_age = now - self._window[0][0]
        if window_age >= self.config.min_window_secs and len(self._window) >= 2:
            baseline_bpm = self._window[0][1]
            rise = bpm - baseline_bpm
            if rise >= self.config.spike_bpm_delta:
                if not self._spike_alerted:
                    self._spike_alerted = True
                    return AlertEvent(
                        type="spike",
                        message=f"Heart rate rose by {rise} BPM in {int(window_age)}s. Rest immediately.",
                        bpm=bpm,
                    )
            else:
                self._spike_alerted = False
        return None

    def calculate_rmssd(self):
        rr = list(self._rr_buffer)
        if len(rr) < 4:
            return None
        diffs = [(rr[i+1] - rr[i]) ** 2 for i in range(len(rr) - 1)]
        return math.sqrt(sum(diffs) / len(diffs)) * 1000
