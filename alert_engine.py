import time
from collections import deque

class AlertEngine:
    """
    Monitors incoming BPM values and detects:
    A) Sustained high HR: > SUSTAINED_THRESHOLD for > SUSTAINED_SECONDS
    B) Sudden spike: rise of >= SPIKE_DELTA BPM within SPIKE_WINDOW seconds
    """

    SUSTAINED_THRESHOLD = 110   # BPM — alert if above this...
    SUSTAINED_SECONDS   = 10    # ...for this many consecutive seconds
    SPIKE_DELTA         = 30    # BPM rise that counts as a POTS spike
    SPIKE_WINDOW        = 30    # seconds to look back for spike detection

    def __init__(self, on_alert_callback):
        """
        on_alert_callback: a function(alert_type, message) that your UI calls
        when an alert is triggered. alert_type is 'sustained' or 'spike'.
        """
        self.on_alert = on_alert_callback
        self.history = deque()          # stores (timestamp, bpm) tuples
        self.high_hr_start = None       # when did high HR begin?
        self.alert_cooldown = 0         # prevent alert spam (30s cooldown)

    def feed(self, bpm: int):
        """Call this every time you get a new BPM reading."""
        now = time.time()
        self.history.append((now, bpm))

        # Clean out readings older than SPIKE_WINDOW
        while self.history and self.history[0][0] < now - self.SPIKE_WINDOW:
            self.history.popleft()

        # === Alert A: Sustained high HR ===
        if bpm > self.SUSTAINED_THRESHOLD:
            if self.high_hr_start is None:
                self.high_hr_start = now  # start the clock
            elif now - self.high_hr_start >= self.SUSTAINED_SECONDS:
                self._trigger('sustained',
                    f"HR has been above {self.SUSTAINED_THRESHOLD} BPM "
                    f"for {int(now - self.high_hr_start)}s. Please rest.")
        else:
            self.high_hr_start = None  # reset if HR drops below threshold

        # === Alert B: Sudden spike (POTS-specific) ===
        if len(self.history) >= 2:
            oldest_bpm = self.history[0][1]
            if bpm - oldest_bpm >= self.SPIKE_DELTA:
                self._trigger('spike',
                    f"Sudden HR spike: +{bpm - oldest_bpm} BPM in "
                    f"{int(now - self.history[0][0])}s. Sit down now.")

    def _trigger(self, alert_type: str, message: str):
        """Internal: fires alert if not in cooldown."""
        now = time.time()
        if now < self.alert_cooldown:
            return  # still in cooldown, skip
        self.alert_cooldown = now + 30  # next alert allowed in 30 seconds
        print(f"[ALERT] {alert_type.upper()}: {message}")
        self.on_alert(alert_type, message)

    def get_resting_hr(self) -> float:
        """Estimate resting HR from the lowest 20% of recent readings."""
        if len(self.history) < 10:
            return 0
        bpms = sorted(r[1] for r in self.history)
        bottom_20pct = bpms[:max(1, len(bpms)//5)]
        return sum(bottom_20pct) / len(bottom_20pct)

    def get_hr_trend(self) -> str:
        """Returns 'rising', 'falling', or 'stable'."""
        if len(self.history) < 6:
            return 'stable'
        recent = [r[1] for r in list(self.history)[-6:]]
        delta = recent[-1] - recent[0]
        if delta > 8:   return 'rising'
        if delta < -8:  return 'falling'
        return 'stable'


# Quick test
if __name__ == "__main__":
    def my_alert(atype, msg):
        print(f">>> ALERT FIRED: [{atype}] {msg}")

    engine = AlertEngine(on_alert_callback=my_alert)

    # Simulate a POTS spike: HR goes from 70 to 105 quickly
    print("Simulating normal HR...")
    for bpm in [68, 70, 72, 70, 71, 69]:
        engine.feed(bpm)
        time.sleep(0.5)

    print("Simulating POTS spike...")
    for bpm in [78, 88, 95, 102, 108, 112]:
        engine.feed(bpm)
        time.sleep(1)

    print(f"Resting HR estimate: {engine.get_resting_hr():.0f} BPM")
    print(f"HR trend: {engine.get_hr_trend()}")
