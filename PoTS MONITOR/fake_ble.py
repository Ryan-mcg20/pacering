import random
from time import time
from kivy.clock import Clock

class SimulatedScenario:
    SCENARIOS = {
        'resting': 'Calm resting HR around 65 BPM',
        'walking': 'Gentle rise to ~85 BPM',
        'pots_spike': 'Sudden spike of 35+ BPM',
        'sustained': 'HR stays above 110 BPM for 15 seconds',
        'recovery': 'HR spikes then slowly recovers',
    }
    def __init__(self, name='resting'):
        self.name = name
        self._start = time()
        self._base = 65
    def get_bpm(self):
        elapsed = time() - self._start
        if self.name == 'resting':
            bpm = self._base + random.randint(-3, 3)
        elif self.name == 'walking':
            bpm = 65 + min(20, elapsed * 0.7) + random.randint(-2, 2)
        elif self.name == 'pots_spike':
            if elapsed < 10:
                bpm = 68 + random.randint(-2, 2)
            elif elapsed < 15:
                bpm = 68 + int((elapsed - 10) * 8) + random.randint(-1, 1)
            else:
                bpm = max(75, 108 - int((elapsed - 15) * 0.8)) + random.randint(-2, 2)
        elif self.name == 'sustained':
            if elapsed < 5:
                bpm = 70 + random.randint(-2, 2)
            else:
                bpm = 115 + random.randint(-3, 3)
        elif self.name == 'recovery':
            if elapsed < 8:
                bpm = 70 + random.randint(-2, 2)
            elif elapsed < 14:
                bpm = 70 + int((elapsed - 8) * 9)
            else:
                decay = min(50, (elapsed - 14) * 0.9)
                bpm = max(72, 124 - int(decay)) + random.randint(-2, 2)
        else:
            bpm = 70
        bpm = max(40, min(200, int(bpm)))
        base_rr = 60.0 / bpm
        rr_intervals = [max(0.3, base_rr + random.gauss(0, 0.015)) for _ in range(2)]
        return bpm, rr_intervals

class FakeBLEWorker:
    def __init__(self, on_bpm, on_status, on_alert, scenario='pots_spike'):
        self.on_bpm = on_bpm
        self.on_status = on_status
        self.on_alert = on_alert
        self.scenario = SimulatedScenario(scenario)
        self._running = False
        from alert_engine import AlertEngine, AlertConfig
        self.alert_engine = AlertEngine(AlertConfig(sustained_hr_threshold=110, sustained_duration_secs=10, spike_bpm_delta=30, spike_window_secs=30))
    def start(self):
        self._running = True
        Clock.schedule_once(self._tick, 0.5)
        Clock.schedule_once(lambda dt: self.on_status('[SIMULATOR] ' + self.scenario.name), 0)
    def stop(self):
        self._running = False
    def _tick(self, dt):
        if not self._running:
            return
        bpm, rr = self.scenario.get_bpm()
        alert = self.alert_engine.update(bpm, rr)
        rmssd = self.alert_engine.calculate_rmssd()
        self.on_bpm(bpm, rmssd)
        if alert:
            self.on_alert(alert)
        Clock.schedule_once(self._tick, 1.0 + random.uniform(-0.05, 0.05))
