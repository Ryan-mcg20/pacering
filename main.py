"""
PaceRing — Heart Rate Monitor for POTS
Main UI file (Kivy, Python)
"""

import json
import os
import time
import threading
from datetime import datetime

# ─── Simulator toggle ───────────────────────────────────────────────
USE_SIMULATOR = True
# ────────────────────────────────────────────────────────────────────

os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.config import Config
Config.set("graphics", "resizable", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.graphics import (
    Color, Rectangle, RoundedRectangle, Line, Ellipse
)
from kivy.metrics import dp, sp
from kivy.properties import (
    NumericProperty, StringProperty, ListProperty,
    BooleanProperty, ObjectProperty
)
from kivy.utils import get_color_from_hex

# ─── Colour palette ─────────────────────────────────────────────────
BG           = get_color_from_hex("#100d1a")
CARD_BG      = get_color_from_hex("#0d0b16")
PILL_BG      = get_color_from_hex("#1e1630")
ACCENT       = get_color_from_hex("#7c3aed")
ACCENT2      = get_color_from_hex("#6c2bda")
TEXT_MAIN    = get_color_from_hex("#ede9fe")
TEXT_MUTED   = get_color_from_hex("#6d5fa0")
BPM_REST     = get_color_from_hex("#ede9fe")
BPM_ELEVATED = get_color_from_hex("#e879f9")
BPM_DANGER   = get_color_from_hex("#f43f5e")
STATUS_GREEN = get_color_from_hex("#4ade80")
STATUS_RED   = get_color_from_hex("#f43f5e")
STATUS_FUCH  = get_color_from_hex("#e879f9")
# ─────────────────────────────────────────────────────────────────────

PROFILE_PATH = os.path.join(
    os.path.expanduser("~"), ".pacering_profile.json"
)

DEV_CODE = "Ryan_5610"

SCENARIOS = ["resting", "walking", "pots_spike", "sustained", "recovery"]

# ─── Helpers ─────────────────────────────────────────────────────────

def hex_to_kivy(h):
    return get_color_from_hex(h)


def load_profile():
    try:
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def save_profile(data):
    try:
        with open(PROFILE_PATH, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def greeting(name):
    h = datetime.now().hour
    if 5 <= h < 12:
        return f"good morning, {name}"
    elif 12 <= h < 17:
        return f"good afternoon, {name}"
    elif 17 <= h < 22:
        return f"good evening, {name}"
    else:
        return f"hey {name}, rest up"


def bpm_colour(bpm, resting, threshold):
    if bpm >= threshold:
        return BPM_DANGER
    elif bpm >= resting + 20:
        return BPM_ELEVATED
    else:
        return BPM_REST


# ─── Reusable styled widgets ─────────────────────────────────────────

class DarkCard(Widget):
    """Rounded dark card background."""
    radius = NumericProperty(dp(16))

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*CARD_BG)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self.radius])


class PillCard(Widget):
    radius = NumericProperty(dp(14))

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PILL_BG)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self.radius])


class PurpleButton(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", ACCENT)
        kw.setdefault("color", TEXT_MAIN)
        kw.setdefault("font_size", sp(16))
        kw.setdefault("bold", True)
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(54))
        super().__init__(**kw)
        with self.canvas.before:
            self._col = Color(*ACCENT)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(27)])
        self.bind(pos=self._upd, size=self._upd)
        self.background_color = [0, 0, 0, 0]

    def _upd(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_press(self):
        self._col.rgba = ACCENT2

    def on_release(self):
        self._col.rgba = ACCENT


class GhostButton(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", [0, 0, 0, 0])
        kw.setdefault("color", TEXT_MUTED)
        kw.setdefault("font_size", sp(15))
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(44))
        super().__init__(**kw)


class StatBox(FloatLayout):
    """Dark pill box with big number + small label."""

    def __init__(self, value="--", label="", **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*PILL_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(14)])
        self.bind(pos=self._upd, size=self._upd)

        self.val_lbl = Label(
            text=str(value),
            font_size=sp(28),
            bold=True,
            color=TEXT_MAIN,
            size_hint=(1, None),
            height=dp(38),
            pos_hint={"center_x": 0.5, "top": 0.72},
        )
        self.lbl = Label(
            text=label,
            font_size=sp(11),
            color=TEXT_MUTED,
            size_hint=(1, None),
            height=dp(18),
            pos_hint={"center_x": 0.5, "top": 0.38},
        )
        self.add_widget(self.val_lbl)
        self.add_widget(self.lbl)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def set_value(self, v, color=None):
        self.val_lbl.text = str(v)
        if color:
            self.val_lbl.color = color


class StepDots(BoxLayout):
    def __init__(self, total=3, current=1, **kw):
        kw.setdefault("orientation", "horizontal")
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (dp(60), dp(12)))
        kw.setdefault("spacing", dp(8))
        super().__init__(**kw)
        self.total = total
        self.current = current
        self._dots = []
        self._build()

    def _build(self):
        self.clear_widgets()
        self._dots = []
        for i in range(1, self.total + 1):
            w = Widget(size_hint=(None, None), size=(dp(10), dp(10)))
            c = ACCENT if i == self.current else TEXT_MUTED
            with w.canvas:
                Color(*c)
                Ellipse(pos=(0, 0), size=(dp(10), dp(10)))
            self._dots.append(w)
            self.add_widget(w)


class StepBadge(Label):
    def __init__(self, text="step 1 of 3", **kw):
        kw.setdefault("text", text)
        kw.setdefault("font_size", sp(12))
        kw.setdefault("color", TEXT_MUTED)
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (dp(100), dp(28)))
        super().__init__(**kw)
        with self.canvas.before:
            Color(*PILL_BG)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PILL_BG)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])


# ─── BPM Graph ───────────────────────────────────────────────────────

class BPMGraph(Widget):
    history = ListProperty([])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, history=self._draw)
        with self.canvas.before:
            Color(*CARD_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(12)])

    def push(self, bpm):
        h = list(self.history)
        h.append(bpm)
        if len(h) > 60:
            h = h[-60:]
        self.history = h

    def _draw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self.canvas.clear()
        with self.canvas.before:
            Color(*CARD_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(12)])
        if len(self.history) < 2:
            return
        pts = self.history
        mn, mx = min(pts), max(pts)
        rng = max(mx - mn, 20)
        w, h = self.size
        pw, ph = self.pos
        pad = dp(10)
        uw = (w - 2 * pad) / (len(pts) - 1)
        points = []
        for i, v in enumerate(pts):
            x = pw + pad + i * uw
            y = ph + pad + ((v - mn) / rng) * (h - 2 * pad)
            points += [x, y]
        with self.canvas:
            Color(*ACCENT, 0.9)
            Line(points=points, width=dp(1.8))


# ─── Onboarding screens ──────────────────────────────────────────────

class OnboardScreen1(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = FloatLayout()
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self._bg, "pos", root.pos),
                  size=lambda *_: setattr(self._bg, "size", root.size))

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(60), dp(32), dp(40)],
            spacing=dp(0),
            size_hint=(1, 1),
        )

        badge = StepBadge(text="  step 1 of 3  ")
        bw = BoxLayout(size_hint_y=None, height=dp(40))
        bw.add_widget(badge)
        bw.add_widget(Widget())
        col.add_widget(bw)

        col.add_widget(Widget(size_hint_y=None, height=dp(40)))

        title = Label(
            text="what's your name?",
            font_size=sp(30),
            bold=True,
            color=TEXT_MAIN,
            size_hint_y=None,
            height=dp(44),
            halign="left",
            valign="middle",
        )
        title.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(title)

        col.add_widget(Widget(size_hint_y=None, height=dp(10)))

        sub = Label(
            text="so we can make this feel like yours",
            font_size=sp(15),
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(26),
            halign="left",
        )
        sub.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(sub)

        col.add_widget(Widget(size_hint_y=None, height=dp(48)))

        self.name_input = TextInput(
            hint_text="your name",
            hint_text_color=TEXT_MUTED,
            foreground_color=TEXT_MAIN,
            background_color=PILL_BG,
            cursor_color=ACCENT,
            font_size=sp(18),
            size_hint_y=None,
            height=dp(56),
            padding=[dp(18), dp(16), dp(18), dp(16)],
            multiline=False,
        )
        col.add_widget(self.name_input)

        col.add_widget(Widget())

        btn = PurpleButton(text="continue")
        btn.bind(on_release=self._next)
        col.add_widget(btn)

        col.add_widget(Widget(size_hint_y=None, height=dp(24)))

        dots_row = BoxLayout(size_hint_y=None, height=dp(20))
        dots_row.add_widget(Widget())
        dots_row.add_widget(StepDots(total=3, current=1))
        dots_row.add_widget(Widget())
        col.add_widget(dots_row)

        root.add_widget(col)
        self.add_widget(root)

    def _next(self, *_):
        name = self.name_input.text.strip() or "friend"
        app = App.get_running_app()
        app.profile["name"] = name
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard2"


class OnboardScreen2(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = FloatLayout()
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self._bg, "pos", root.pos),
                  size=lambda *_: setattr(self._bg, "size", root.size))

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(60), dp(32), dp(40)],
            spacing=dp(0),
            size_hint=(1, 1),
        )

        badge = StepBadge(text="  step 2 of 3  ")
        bw = BoxLayout(size_hint_y=None, height=dp(40))
        bw.add_widget(badge)
        bw.add_widget(Widget())
        col.add_widget(bw)

        col.add_widget(Widget(size_hint_y=None, height=dp(36)))

        title = Label(
            text="your resting heart rate",
            font_size=sp(28),
            bold=True,
            color=TEXT_MAIN,
            size_hint_y=None,
            height=dp(44),
            halign="left",
        )
        title.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(title)

        col.add_widget(Widget(size_hint_y=None, height=dp(8)))

        sub = Label(
            text="used to detect spikes accurately",
            font_size=sp(15),
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(26),
            halign="left",
        )
        sub.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(sub)

        col.add_widget(Widget(size_hint_y=None, height=dp(36)))

        boxes = GridLayout(
            cols=2,
            spacing=dp(12),
            size_hint_y=None,
            height=dp(90),
        )
        self.box_resting = StatBox(value="65", label="resting BPM")
        self.box_threshold = StatBox(value="110", label="alert threshold")
        boxes.add_widget(self.box_resting)
        boxes.add_widget(self.box_threshold)
        col.add_widget(boxes)

        col.add_widget(Widget(size_hint_y=None, height=dp(28)))

        self.slider = Slider(
            min=40, max=100, value=65,
            size_hint_y=None, height=dp(44),
            cursor_size=(dp(28), dp(28)),
        )
        self.slider.bind(value=self._slider_changed)
        col.add_widget(self.slider)

        drag_lbl = Label(
            text="drag to set your resting BPM",
            font_size=sp(13),
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(22),
        )
        col.add_widget(drag_lbl)

        col.add_widget(Widget())

        btn = PurpleButton(text="continue")
        btn.bind(on_release=self._next)
        col.add_widget(btn)

        col.add_widget(Widget(size_hint_y=None, height=dp(6)))

        ghost = GhostButton(text="use defaults")
        ghost.bind(on_release=self._defaults)
        col.add_widget(ghost)

        col.add_widget(Widget(size_hint_y=None, height=dp(16)))

        dots_row = BoxLayout(size_hint_y=None, height=dp(20))
        dots_row.add_widget(Widget())
        dots_row.add_widget(StepDots(total=3, current=2))
        dots_row.add_widget(Widget())
        col.add_widget(dots_row)

        root.add_widget(col)
        self.add_widget(root)

    def _slider_changed(self, _, val):
        r = int(val)
        t = r + 45
        self.box_resting.set_value(str(r))
        self.box_threshold.set_value(str(t))

    def _next(self, *_):
        app = App.get_running_app()
        app.profile["resting_bpm"] = int(self.slider.value)
        app.profile["threshold"] = int(self.slider.value) + 45
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard3"

    def _defaults(self, *_):
        app = App.get_running_app()
        app.profile["resting_bpm"] = 65
        app.profile["threshold"] = 110
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard3"


class OnboardScreen3(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = FloatLayout()
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self._bg, "pos", root.pos),
                  size=lambda *_: setattr(self._bg, "size", root.size))

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(60), dp(32), dp(40)],
            spacing=dp(0),
            size_hint=(1, 1),
        )

        badge = StepBadge(text="  step 3 of 3  ")
        bw = BoxLayout(size_hint_y=None, height=dp(40))
        bw.add_widget(badge)
        bw.add_widget(Widget())
        col.add_widget(bw)

        col.add_widget(Widget(size_hint_y=None, height=dp(36)))

        title = Label(
            text="spike sensitivity",
            font_size=sp(30),
            bold=True,
            color=TEXT_MAIN,
            size_hint_y=None,
            height=dp(44),
            halign="left",
        )
        title.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(title)

        col.add_widget(Widget(size_hint_y=None, height=dp(8)))

        sub = Label(
            text="alert me when HR rises by...",
            font_size=sp(15),
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(26),
            halign="left",
        )
        sub.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(sub)

        col.add_widget(Widget(size_hint_y=None, height=dp(36)))

        boxes = GridLayout(
            cols=2,
            spacing=dp(12),
            size_hint_y=None,
            height=dp(90),
        )
        self.box_delta = StatBox(value="+30", label="BPM spike delta")
        self.box_dur = StatBox(value="10s", label="sustained duration")
        boxes.add_widget(self.box_delta)
        boxes.add_widget(self.box_dur)
        col.add_widget(boxes)

        col.add_widget(Widget(size_hint_y=None, height=dp(28)))

        self.slider = Slider(
            min=15, max=50, value=30,
            size_hint_y=None, height=dp(44),
            cursor_size=(dp(28), dp(28)),
        )
        self.slider.bind(value=self._slider_changed)
        col.add_widget(self.slider)

        drag_lbl = Label(
            text="matches typical POTS thresholds",
            font_size=sp(13),
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(22),
        )
        col.add_widget(drag_lbl)

        col.add_widget(Widget())

        btn = PurpleButton(text="let's go")
        btn.bind(on_release=self._finish)
        col.add_widget(btn)

        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        dots_row = BoxLayout(size_hint_y=None, height=dp(20))
        dots_row.add_widget(Widget())
        dots_row.add_widget(StepDots(total=3, current=3))
        dots_row.add_widget(Widget())
        col.add_widget(dots_row)

        root.add_widget(col)
        self.add_widget(root)

    def _slider_changed(self, _, val):
        self.box_delta.set_value(f"+{int(val)}")

    def _finish(self, *_):
        app = App.get_running_app()
        app.profile["spike_delta"] = int(self.slider.value)
        app.profile["spike_duration"] = 10
        app.profile["vibration"] = True
        app.profile["sound_alerts"] = True
        save_profile(app.profile)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "monitor"
        app.root.get_screen("monitor").start_monitoring()


# ─── Main monitor screen ─────────────────────────────────────────────

class MonitorScreen(Screen):
    current_bpm = NumericProperty(0)
    current_hrv = NumericProperty(0)
    status_text = StringProperty("not connected")
    alert_visible = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._alert_card = None
        self._dev_taps = []
        self._sim = None
        self._connected = False
        self._bpm_color = list(BPM_REST)
        self._alert_animated = False
        self._build()

    def _build(self):
        root = FloatLayout()
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self._bg, "pos", root.pos),
                  size=lambda *_: setattr(self._bg, "size", root.size))

        # Main scroll content
        main_col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(50), dp(24), dp(24)],
            spacing=dp(16),
            size_hint=(1, 1),
        )

        # Top bar
        top_row = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )
        self.greeting_lbl = Label(
            text="good morning",
            font_size=sp(18),
            bold=True,
            color=TEXT_MAIN,
            halign="left",
            valign="middle",
        )
        self.greeting_lbl.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        top_row.add_widget(self.greeting_lbl)

        self.initial_btn = Button(
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_normal="",
            background_color=[0, 0, 0, 0],
        )
        with self.initial_btn.canvas.before:
            Color(*ACCENT)
            self._init_circle = Ellipse(
                pos=self.initial_btn.pos,
                size=self.initial_btn.size,
            )
        self.initial_btn.bind(
            pos=lambda *_: setattr(
                self._init_circle, "pos", self.initial_btn.pos
            ),
            size=lambda *_: setattr(
                self._init_circle, "size", self.initial_btn.size
            ),
            on_release=self._initial_tapped,
        )
        self.initial_lbl = Label(
            text="?",
            font_size=sp(16),
            bold=True,
            color=TEXT_MAIN,
            size_hint=(None, None),
            size=(dp(40), dp(40)),
        )
        top_row.add_widget(self.initial_btn)
        top_row.add_widget(self.initial_lbl)
        main_col.add_widget(top_row)

        # Connection status
        self.status_lbl = Label(
            text="not connected",
            font_size=sp(13),
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(20),
            halign="left",
        )
        self.status_lbl.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        main_col.add_widget(self.status_lbl)

        # BPM display
        bpm_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(130),
            spacing=dp(2),
        )
        self.bpm_lbl = Label(
            text="--",
            font_size=sp(96),
            bold=True,
            color=BPM_REST,
            size_hint_y=None,
            height=dp(100),
        )
        bpm_unit = Label(
            text="BPM",
            font_size=sp(14),
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(20),
        )
        bpm_box.add_widget(self.bpm_lbl)
        bpm_box.add_widget(bpm_unit)
        main_col.add_widget(bpm_box)

        # HRV
        self.hrv_lbl = Label(
            text="HRV  --  ms",
            font_size=sp(15),
            color=TEXT_MAIN,
            size_hint_y=None,
            height=dp(24),
        )
        main_col.add_widget(self.hrv_lbl)

        # Graph
        self.graph = BPMGraph(
            size_hint_y=None,
            height=dp(90),
        )
        main_col.add_widget(self.graph)

        # Stats row
        stats_row = GridLayout(
            cols=3,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(84),
        )
        self.stat_resting = StatBox(value="--", label="resting baseline")
        self.stat_hrv = StatBox(value="--", label="HRV ms")
        self.stat_status = StatBox(value="clear", label="status")
        self.stat_status.val_lbl.color = STATUS_GREEN
        stats_row.add_widget(self.stat_resting)
        stats_row.add_widget(self.stat_hrv)
        stats_row.add_widget(self.stat_status)
        main_col.add_widget(stats_row)

        main_col.add_widget(Widget())

        # Connect button
        self.connect_btn = PurpleButton(text="connect to band")
        self.connect_btn.bind(on_release=self._connect_pressed)
        main_col.add_widget(self.connect_btn)

        root.add_widget(main_col)

        # Alert card (hidden, slides up)
        self._alert_card = self._build_alert_card()
        self._alert_card.y = -dp(200)
        root.add_widget(self._alert_card)

        self.add_widget(root)
        self._root_layout = root
        self._main_col = main_col

    def _build_alert_card(self):
        card = FloatLayout(
            size_hint=(1, None),
            height=dp(180),
        )
        card.y = -dp(200)

        with card.canvas.before:
            Color(*CARD_BG)
            self._card_bg = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[dp(20), dp(20), 0, 0]
            )
            Color(*ACCENT, 0.5)
            self._card_border = Line(
                rounded_rectangle=[
                    card.x, card.y, card.width, card.height, dp(20)
                ],
                width=dp(1.2),
            )

        card.bind(pos=self._upd_card_bg, size=self._upd_card_bg)

        inner = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(20), dp(24), dp(16)],
            spacing=dp(8),
            size_hint=(1, 1),
        )
        self.alert_title = Label(
            text="spike detected",
            font_size=sp(18),
            bold=True,
            color=TEXT_MAIN,
            halign="left",
            size_hint_y=None,
            height=dp(28),
        )
        self.alert_title.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        self.alert_msg = Label(
            text="",
            font_size=sp(14),
            color=TEXT_MUTED,
            halign="left",
            size_hint_y=None,
            height=dp(40),
        )
        self.alert_msg.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, dp(40)))
        )
        dismiss_btn = PurpleButton(text="ok — resting now", height=dp(46))
        dismiss_btn.bind(on_release=self._dismiss_alert)

        inner.add_widget(self.alert_title)
        inner.add_widget(self.alert_msg)
        inner.add_widget(dismiss_btn)
        card.add_widget(inner)
        return card

    def _upd_card_bg(self, *_):
        c = self._alert_card
        self._card_bg.pos = c.pos
        self._card_bg.size = c.size
        self._card_border.rounded_rectangle = [
            c.x, c.y, c.width, c.height, dp(20)
        ]

    def on_enter(self):
        self._refresh_profile()

    def _refresh_profile(self):
        app = App.get_running_app()
        p = app.profile
        name = p.get("name", "friend")
        self.greeting_lbl.text = greeting(name)
        initial = name[0].upper() if name else "?"
        self.initial_lbl.text = initial
        resting = p.get("resting_bpm", 65)
        self.stat_resting.set_value(str(resting))

    def start_monitoring(self):
        self._refresh_profile()
        if USE_SIMULATOR:
            self._start_simulator("resting")
        else:
            self._start_ble()

    def _start_simulator(self, scenario="resting"):
        try:
            from fake_ble import FakeBLE
            if self._sim:
                self._sim.stop()
            self._sim = FakeBLE(scenario=scenario)
            self._sim.start(self._on_bpm_data)
            self.status_lbl.text = f"simulator — {scenario}"
            self._connected = True
        except Exception as e:
            self.status_lbl.text = f"sim error: {e}"

    def _start_ble(self):
        try:
            from ble_manager import BLEManager
            self._ble = BLEManager()
            self._ble.connect(self._on_bpm_data, self._on_ble_status)
            self.status_lbl.text = "scanning for band..."
        except Exception as e:
            self.status_lbl.text = f"ble error: {e}"

    def _on_bpm_data(self, bpm, hrv=None):
        Clock.schedule_once(lambda dt: self._update_display(bpm, hrv))

    def _on_ble_status(self, status):
        Clock.schedule_once(lambda dt: setattr(
            self.status_lbl, "text", status
        ))

    def _update_display(self, bpm, hrv=None):
        app = App.get_running_app()
        p = app.profile
        resting = p.get("resting_bpm", 65)
        threshold = p.get("threshold", 110)

        # BPM label
        self.bpm_lbl.text = str(bpm)
        target_col = bpm_colour(bpm, resting, threshold)
        anim = Animation(color=target_col, duration=0.4)
        anim.start(self.bpm_lbl)

        # HRV
        if hrv is not None:
            self.hrv_lbl.text = f"HRV  {hrv}  ms"
            self.stat_hrv.set_value(str(hrv))

        # Graph
        self.graph.push(bpm)

        # Status box
        if bpm >= threshold:
            self.stat_status.set_value("alert", STATUS_RED)
        elif bpm >= resting + 20:
            self.stat_status.set_value("recovering", STATUS_FUCH)
        else:
            self.stat_status.set_value("clear", STATUS_GREEN)

        # Alert engine check
        try:
            from alert_engine import AlertEngine
            if not hasattr(self, "_alert_engine"):
                self._alert_engine = AlertEngine(p)
            result = self._alert_engine.check(bpm)
            if result and not self._alert_animated:
                self._show_alert(result)
        except Exception:
            pass

    def _show_alert(self, result):
        self._alert_animated = True
        title = result.get("title", "spike detected")
        msg = result.get("message", "your heart rate spiked.")
        self.alert_title.text = title
        self.alert_msg.text = msg
        target_y = dp(0)
        anim = Animation(y=target_y, duration=0.35, t="out_back")
        anim.start(self._alert_card)

    def _dismiss_alert(self, *_):
        anim = Animation(y=-dp(200), duration=0.25, t="in_quad")
        anim.bind(on_complete=lambda *_: setattr(
            self, "_alert_animated", False
        ))
        anim.start(self._alert_card)
        try:
            from alert_engine import AlertEngine
            if hasattr(self, "_alert_engine"):
                self._alert_engine.reset()
        except Exception:
            pass

    def _connect_pressed(self, *_):
        self.connect_btn.text = "connecting..."
        self.connect_btn.disabled = True
        Clock.schedule_once(self._do_connect, 0.1)

    def _do_connect(self, *_):
        self.start_monitoring()
        self.connect_btn.text = "connected"

    def _initial_tapped(self, *_):
        now = time.time()
        self._dev_taps = [t for t in self._dev_taps if now - t < 1.5]
        self._dev_taps.append(now)
        if len(self._dev_taps) >= 5:
            self._dev_taps = []
            self._open_dev_mode()
        else:
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = "settings"

    def _open_dev_mode(self):
        content = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(20)],
            spacing=dp(12),
        )
        with content.canvas.before:
            Color(*CARD_BG)
            Rectangle(pos=content.pos, size=content.size)

        lbl = Label(
            text="developer code",
            font_size=sp(16),
            color=TEXT_MAIN,
            size_hint_y=None,
            height=dp(30),
        )
        self._dev_input = TextInput(
            hint_text="enter code",
            hint_text_color=TEXT_MUTED,
            foreground_color=TEXT_MAIN,
            background_color=PILL_BG,
            cursor_color=ACCENT,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(48),
            multiline=False,
            password=True,
        )
        self._dev_err = Label(
            text="",
            font_size=sp(13),
            color=STATUS_RED,
            size_hint_y=None,
            height=dp(22),
        )
        ok_btn = PurpleButton(text="unlock")
        ok_btn.bind(on_release=self._check_dev_code)

        content.add_widget(lbl)
        content.add_widget(self._dev_input)
        content.add_widget(self._dev_err)
        content.add_widget(ok_btn)

        self._dev_popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, None),
            height=dp(260),
            background_color=CARD_BG,
            separator_height=0,
            title_size=0,
        )
        self._dev_popup.open()

    def _check_dev_code(self, *_):
        code = self._dev_input.text.strip()
        if code == DEV_CODE:
            self._dev_popup.dismiss()
            self._open_scenario_picker()
        else:
            self._dev_input.text = ""
            self._dev_err.text = "wrong code — try again"

    def _open_scenario_picker(self):
        content = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(16)],
            spacing=dp(10),
        )
        with content.canvas.before:
            Color(*CARD_BG)
            Rectangle(pos=content.pos, size=content.size)

        content.add_widget(Label(
            text="select scenario",
            font_size=sp(16),
            bold=True,
            color=TEXT_MAIN,
            size_hint_y=None,
            height=dp(30),
        ))

        for sc in SCENARIOS:
            btn = PurpleButton(text=sc, height=dp(42))
            btn.scenario = sc
            btn.bind(on_release=self._pick_scenario)
            content.add_widget(btn)

        self._scenario_popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, None),
            height=dp(380),
            background_color=CARD_BG,
            separator_height=0,
            title_size=0,
        )
        self._scenario_popup.open()

    def _pick_scenario(self, btn):
        self._scenario_popup.dismiss()
        sc = btn.scenario
        self._alert_animated = False
        self._start_simulator(sc)


# ─── Settings screen ────────────────────────────────────────────────

class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = FloatLayout()
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self._bg, "pos", root.pos),
                  size=lambda *_: setattr(self._bg, "size", root.size))

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(50), dp(24), dp(30)],
            spacing=dp(0),
            size_hint=(1, 1),
        )

        # Back button
        back_row = BoxLayout(size_hint_y=None, height=dp(40))
        back_btn = GhostButton(
            text="← back",
            size_hint=(None, 1),
            width=dp(80),
        )
        back_btn.bind(on_release=self._back)
        back_row.add_widget(back_btn)
        back_row.add_widget(Widget())
        col.add_widget(back_row)

        col.add_widget(Widget(size_hint_y=None, height=dp(12)))

        heading = Label(
            text="profile",
            font_size=sp(26),
            bold=True,
            color=TEXT_MAIN,
            size_hint_y=None,
            height=dp(40),
            halign="left",
        )
        heading.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(heading)

        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self._rows_container = BoxLayout(
            orientation="vertical",
            spacing=dp(2),
            size_hint_y=None,
        )
        self._rows_container.bind(
            minimum_height=self._rows_container.setter("height")
        )
        col.add_widget(self._rows_container)

        col.add_widget(Widget())

        back_btn2 = PurpleButton(text="back to monitor")
        back_btn2.bind(on_release=self._back)
        col.add_widget(back_btn2)

        root.add_widget(col)
        self.add_widget(root)

    def on_enter(self):
        self._refresh()

    def _refresh(self):
        app = App.get_running_app()
        p = app.profile
        self._rows_container.clear_widgets()

        rows = [
            ("name", p.get("name", "--")),
            ("resting BPM", str(p.get("resting_bpm", 65))),
            ("alert threshold", str(p.get("threshold", 110))),
            ("spike delta", f"+{p.get('spike_delta', 30)}"),
            ("vibration", "on" if p.get("vibration", True) else "off"),
            ("sound alerts", "on" if p.get("sound_alerts", True) else "off"),
        ]
        for label, val in rows:
            row = BoxLayout(
                size_hint_y=None,
                height=dp(52),
                padding=[dp(16), 0, dp(16), 0],
            )
            with row.canvas.before:
                Color(*PILL_BG)
                RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(10)])
            row.bind(
                pos=lambda w, _: w.canvas.before.clear() or _draw_row(w),
                size=lambda w, _: w.canvas.before.clear() or _draw_row(w),
            )
            lbl = Label(
                text=label,
                font_size=sp(14),
                color=TEXT_MAIN,
                halign="left",
                valign="middle",
            )
            lbl.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
            val_lbl = Label(
                text=val,
                font_size=sp(14),
                color=TEXT_MUTED,
                halign="right",
                valign="middle",
            )
            val_lbl.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
            row.add_widget(lbl)
            row.add_widget(val_lbl)
            self._rows_container.add_widget(row)
            self._rows_container.add_widget(
                Widget(size_hint_y=None, height=dp(6))
            )

    def _back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "monitor"


def _draw_row(w):
    with w.canvas.before:
        Color(*PILL_BG)
        RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(10)])


# ─── App ────────────────────────────────────────────────────────────

class PaceRingApp(App):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.profile = {
            "name": "friend",
            "resting_bpm": 65,
            "threshold": 110,
            "spike_delta": 30,
            "spike_duration": 10,
            "vibration": True,
            "sound_alerts": True,
        }

    def build(self):
        Window.clearcolor = BG

        saved = load_profile()
        if saved:
            self.profile.update(saved)

        sm = ScreenManager()
        sm.add_widget(OnboardScreen1(name="onboard1"))
        sm.add_widget(OnboardScreen2(name="onboard2"))
        sm.add_widget(OnboardScreen3(name="onboard3"))
        sm.add_widget(MonitorScreen(name="monitor"))
        sm.add_widget(SettingsScreen(name="settings"))

        if saved and saved.get("name"):
            sm.current = "monitor"
            Clock.schedule_once(
                lambda dt: sm.get_screen("monitor").start_monitoring(), 0.5
            )
        else:
            sm.current = "onboard1"

        return sm


if __name__ == "__main__":
    PaceRingApp().run()
