# PaceRing Full App

import json, os, random, time
from collections import deque

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import *
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.utils import get_color_from_hex
from kivy.animation import Animation

# ---------------- CONFIG ----------------
USE_SIMULATOR = True
PROFILE_FILE = "profile.json"

# ---------------- COLORS ----------------
BG = get_color_from_hex("#100d1a")
CARD = get_color_from_hex("#0d0b16")
PURPLE = get_color_from_hex("#7c3aed")
LILAC = get_color_from_hex("#ede9fe")
MUTED = get_color_from_hex("#6d5fa0")
FUCH = get_color_from_hex("#e879f9")
RED = get_color_from_hex("#f43f5e")
GREEN = get_color_from_hex("#4ade80")

# ---------------- SIMULATOR ----------------
class Simulator:
    def __init__(self):
        self.mode = "resting"
        self.bpm = 65
        self.start_time = time.time()

    def set_mode(self, mode):
        self.mode = mode
        self.start_time = time.time()

    def update(self):
        t = time.time() - self.start_time

        if self.mode == "resting":
            self.bpm = 65 + random.randint(-2, 2)

        elif self.mode == "walking":
            self.bpm = 80 + random.randint(-3, 3)

        elif self.mode == "pots_spike":
            self.bpm = 65 + int(min(40, t * 10))

        elif self.mode == "sustained":
            self.bpm = 115 + random.randint(-3, 3)

        elif self.mode == "recovery":
            self.bpm = 120 - int(t * 5)
            if self.bpm < 70:
                self.bpm = 70

        return int(self.bpm)

# ---------------- ALERT ENGINE ----------------
class AlertEngine:
    def __init__(self, resting, delta):
        self.resting = resting
        self.delta = delta
        self.last_trigger = 0
        self.above_time = 0

    def check(self, bpm):
        now = time.time()
        if bpm > self.resting + self.delta:
            if self.above_time == 0:
                self.above_time = now
            if now - self.above_time > 10:
                return "sustained"
            return "spike"
        else:
            self.above_time = 0
        return None

# ---------------- SCREENS ----------------
class NameScreen(Screen): pass
class HRScreen(Screen): pass
class SensScreen(Screen): pass

class MonitorScreen(Screen):
    bpm = NumericProperty(65)
    hrv = NumericProperty(40)
    status = StringProperty("not connected")
    greeting = StringProperty("")
    name = StringProperty("")
    alert_text = StringProperty("")
    show_alert = BooleanProperty(False)

# ---------------- MANAGER ----------------
class Manager(ScreenManager): pass

# ---------------- KV ----------------
KV = """
<Label>:
    color: 1,1,1,1

Manager:
    NameScreen:
    HRScreen:
    SensScreen:
    MonitorScreen:

<NameScreen>:
    name: "name"
    BoxLayout:
        orientation: "vertical"
        padding: 40
        spacing: 20

        Label:
            text: "step 1 of 3"
            color: 0.8,0.7,1,1

        Label:
            text: "what's your name?"
            font_size: 26

        TextInput:
            id: name_input
            hint_text: "your name"
            background_color: 0.1,0.08,0.2,1

        Button:
            text: "continue"
            background_color: 0.5,0.2,1,1
            on_release:
                app.profile["name"] = name_input.text
                root.manager.current = "hr"

<HRScreen>:
    name: "hr"
    resting: 65

    BoxLayout:
        orientation: "vertical"
        padding: 40
        spacing: 20

        Label:
            text: "your resting heart rate"

        Slider:
            min: 40
            max: 100
            value: root.resting
            on_value: root.resting = int(self.value)

        Label:
            text: str(root.resting) + " BPM"

        Button:
            text: "continue"
            on_release:
                app.profile["resting"] = root.resting
                root.manager.current = "sens"

<SensScreen>:
    name: "sens"
    delta: 30

    BoxLayout:
        orientation: "vertical"
        padding: 40
        spacing: 20

        Label:
            text: "spike sensitivity"

        Slider:
            min: 15
            max: 50
            value: root.delta
            on_value: root.delta = int(self.value)

        Label:
            text: "+" + str(root.delta)

        Button:
            text: "lets go"
            on_release:
                app.profile["delta"] = root.delta
                app.save_profile()
                app.start_monitor()

<MonitorScreen>:
    name: "monitor"

    FloatLayout:

        Label:
            text: root.greeting
            pos_hint: {"top":1}
            size_hint: 1,0.1

        Label:
            text: root.status
            pos_hint: {"top":0.9}
            font_size: 14

        Label:
            text: str(root.bpm)
            font_size: 90
            pos_hint: {"center_y":0.5}

        Label:
            text: "BPM"
            pos_hint: {"center_y":0.4}

        Label:
            text: "HRV " + str(root.hrv)
            pos_hint: {"center_y":0.3}

        BoxLayout:
            size_hint: 1,0.2
            pos_hint: {"y":0}

            Button:
                text: "connect to band"
                on_release: app.connect()

        BoxLayout:
            size_hint: 1,0.3
            pos_hint: {"y":-0.3 if not root.show_alert else 0}

            canvas.before:
                Color:
                    rgba: 0.1,0,0.2,1
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                text: root.alert_text

            Button:
                text: "ok - resting now"
                on_release: app.dismiss_alert()
"""

# ---------------- APP ----------------
class PaceRing(App):

    def build(self):
        self.profile = {}
        self.sim = Simulator()
        self.load_profile()

        self.root = Builder.load_string(KV)

        if self.profile:
            self.start_monitor()

        return self.root

    def get_greeting(self):
        h = time.localtime().tm_hour
        name = self.profile.get("name", "")
        if h < 12:
            return f"good morning, {name}"
        elif h < 18:
            return f"good afternoon, {name}"
        else:
            return f"good evening, {name}"

    def start_monitor(self):
        self.root.current = "monitor"
        screen = self.root.get_screen("monitor")

        screen.name = self.profile["name"]
        screen.greeting = self.get_greeting()
        screen.status = "connected — monitoring"

        self.alert_engine = AlertEngine(
            self.profile["resting"],
            self.profile["delta"]
        )

        self.graph = deque(maxlen=60)

        Clock.schedule_interval(self.update, 1)

    def connect(self):
        self.root.get_screen("monitor").status = "connecting..."

    def update(self, dt):
        bpm = self.sim.update()
        screen = self.root.get_screen("monitor")

        screen.bpm = bpm
        screen.hrv = random.randint(30, 60)

        alert = self.alert_engine.check(bpm)
        if alert:
            screen.alert_text = alert + " detected"
            screen.show_alert = True

    def dismiss_alert(self):
        self.root.get_screen("monitor").show_alert = False

    def save_profile(self):
        with open(PROFILE_FILE, "w") as f:
            json.dump(self.profile, f)

    def load_profile(self):
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r") as f:
                self.profile = json.load(f)

if __name__ == "__main__":
    PaceRing().run()
