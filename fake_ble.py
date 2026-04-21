import random, math
from time import time
from kivy.clock import Clock

class SimulatedScenario:
    SCENARIOS = {
        'resting':    'Calm resting HR ~65 BPM',
        'walking':    'Gentle rise to ~85 BPM',
        'pots_spike': 'Sudden spike 35+ BPM',
        'sustained':  'HR stays above 110 BPM',
        'recovery':   'Spike then slow recovery',
    }
    def __init__(self, name='resting'):
        self.name = name
        self._start = time()
    def get_bpm(self):
        e = time() - self._start
        if self.name == 'resting':
            bpm = 65 + random.randint(-3, 3)
        elif self.name == 'walking':
            bpm = int(65 + min(20, e * 0.7)) + random.randint(-2, 2)
        elif self.name == 'pots_spike':
            if e < 10: bpm = 68 + random.randint(-2, 2)
            elif e < 15: bpm = 68 + int((e-10)*8) + random.randint(-1,1)
            else: bpm = max(75, 108 - int((e-15)*0.8)) + random.randint(-2,2)
        elif self.name == 'sustained':
            bpm = 115 + random.randint(-3,3) if e > 5 else 70 + random.randint(-2,2)
        elif self.name == 'recovery':
            if e < 8: bpm = 70 + random.randint(-2,2)
            elif e < 14: bpm = 70 + int((e-8)*9)
            else: bpm = max(72, 124 - int((e-14)*0.9)) + random.randint(-2,2)
        else: bpm = 70
        bpm = max(40, min(200, int(bpm)))
        base_rr = 60.0/bpm
        return bpm, [max(0.3, base_rr + random.gauss(0,0.015)) for _ in range(2)]

class FakeBLEWorker:
    def __init__(self, on_bpm, on_status, on_alert, scenario='resting'):
        self.on_bpm = on_bpm
        self.on_status = on_status
        self.on_alert = on_alert
        self.scenario = SimulatedScenario(scenario)
        self._running = False
        from alert_engine import AlertEngine, AlertConfig
        self.alert_engine = AlertEngine(AlertConfig())
    def start(self):
        self._running = True
        Clock.schedule_once(self._tick, 0.5)
        Clock.schedule_once(lambda dt: self.on_status('[SIM] ' + self.scenario.name), 0)
    def stop(self):
        self._running = False
    def _tick(self, dt):
        if not self._running: return
        bpm, rr = self.scenario.get_bpm()
        alert = self.alert_engine.update(bpm, rr)
        rmssd = self.alert_engine.calculate_rmssd()
        self.on_bpm(bpm, rmssd)
        if alert: self.on_alert(alert)
        Clock.schedule_once(self._tick, 1.0 + random.uniform(-0.05, 0.05))
