"""
PaceRing v4.0 — POTS Heart Rate Monitor
Animated heart background, weekly summary, full dev mode
"""

import json, os, time, math, random
from datetime import datetime, timedelta
from collections import deque

USE_SIMULATOR = True   # <-- Toggle here, or via dev mode in-app

os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.config import Config
Config.set("graphics", "resizable", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.graphics import (
    Color, Rectangle, RoundedRectangle, Line, Ellipse,
    PushMatrix, PopMatrix, Scale, Translate, Mesh,
)
from kivy.metrics import dp, sp
from kivy.properties import (
    NumericProperty, StringProperty, ListProperty, BooleanProperty,
)
from kivy.utils import get_color_from_hex

# ── Palette ────────────────────────────────────────────────────────────────────
BG          = get_color_from_hex("#100d1a")
CARD_BG     = get_color_from_hex("#0d0b16")
PILL_BG     = get_color_from_hex("#1e1630")
ACCENT      = get_color_from_hex("#7c3aed")
ACCENT2     = get_color_from_hex("#6c2bda")
TEXT_MAIN   = get_color_from_hex("#ede9fe")
TEXT_MUTED  = get_color_from_hex("#6d5fa0")
BPM_REST    = get_color_from_hex("#ede9fe")
BPM_ELEV    = get_color_from_hex("#e879f9")
BPM_DANGER  = get_color_from_hex("#f43f5e")
STATUS_GRN  = get_color_from_hex("#4ade80")
STATUS_RED  = get_color_from_hex("#f43f5e")
STATUS_FUCH = get_color_from_hex("#e879f9")
AMBER       = get_color_from_hex("#fb923c")

PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".pacering_profile.json")
LOG_PATH     = os.path.join(os.path.expanduser("~"), ".pacering_log.json")
DEV_CODE     = "Ryan_5610"
SCENARIOS    = ["resting", "walking", "pots_spike", "sustained", "recovery"]

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_profile():
    try:
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH) as f:
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

def load_log():
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def append_log(entry):
    log = load_log()
    log.append(entry)
    log = log[-10000:]  # keep last 10k entries
    try:
        with open(LOG_PATH, "w") as f:
            json.dump(log, f)
    except Exception:
        pass

def greeting(name):
    h = datetime.now().hour
    if 5 <= h < 12:    return f"good morning, {name}"
    elif 12 <= h < 17: return f"good afternoon, {name}"
    elif 17 <= h < 22: return f"good evening, {name}"
    else:              return f"hey {name}, rest up"

def bpm_colour(bpm, resting, threshold):
    if bpm >= threshold:       return list(BPM_DANGER)
    elif bpm >= resting + 20:  return list(BPM_ELEV)
    else:                      return list(BPM_REST)

def _pill_bg(w):
    w.canvas.before.clear()
    with w.canvas.before:
        Color(*PILL_BG)
        RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(10)])

# ── Animated Heart Widget ──────────────────────────────────────────────────────

class HeartWidget(Widget):
    """
    Draws a stylised anatomical-style heart using bezier curves.
    Pulses at the current BPM rate.
    """
    pulse_scale = NumericProperty(1.0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._bpm = 65
        self._pulse_event = None
        self._beat_phase = 0.0
        self.bind(pos=self._draw, size=self._draw, pulse_scale=self._draw)

    def set_bpm(self, bpm):
        self._bpm = max(40, min(200, bpm))
        # Restart pulse timer at new rate
        if self._pulse_event:
            self._pulse_event.cancel()
        interval = 60.0 / self._bpm
        self._pulse_event = Clock.schedule_interval(self._pulse_tick, interval)

    def _pulse_tick(self, dt):
        # Quick systole (expand) then diastole (contract)
        anim = (
            Animation(pulse_scale=1.18, duration=0.12, t="out_quad") +
            Animation(pulse_scale=0.96, duration=0.08, t="in_quad") +
            Animation(pulse_scale=1.0,  duration=0.15, t="out_quad")
        )
        anim.start(self)

    def _draw(self, *_):
        self.canvas.clear()
        cx = self.center_x
        cy = self.center_y
        s  = self.pulse_scale
        r  = min(self.width, self.height) * 0.42 * s

        with self.canvas:
            # Outer glow rings
            Color(0.49, 0.23, 0.93, 0.06 * s)
            Ellipse(pos=(cx - r*1.5, cy - r*1.5), size=(r*3, r*3))
            Color(0.49, 0.23, 0.93, 0.10 * s)
            Ellipse(pos=(cx - r*1.2, cy - r*1.2), size=(r*2.4, r*2.4))

            # Main heart shape via bezier approximation using Line
            # Heart parametric: x = 16sin^3(t), y = 13cos(t)-5cos(2t)-2cos(3t)-cos(4t)
            pts = []
            steps = 80
            for i in range(steps + 1):
                t = (i / steps) * 2 * math.pi
                hx = 16 * (math.sin(t)**3)
                hy = 13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t)
                # Normalize: hx in [-16,16], hy in [-17, 13]
                nx = cx + (hx / 17.0) * r
                ny = cy + (hy / 17.0) * r
                pts.extend([nx, ny])

            # Dark filled heart (draw as filled polygon via mesh)
            verts = []
            for i in range(0, len(pts), 2):
                verts.extend([pts[i], pts[i+1], 0, 0])
            # Centre point
            verts.extend([cx, cy, 0, 0])
            n = len(verts) // 4
            indices = list(range(n-1)) + [n-1] * (n-1)
            # Simplified: draw as outline + filled with translucent
            Color(0.35, 0.08, 0.55, 0.55)
            Mesh(vertices=verts[:-4], indices=list(range(n-1)), mode='triangle_fan')

            # Heart outline — fuchsia/purple gradient feel
            Color(0.91, 0.475, 0.976, 0.85)
            Line(points=pts, width=dp(1.8), close=True)

            # Inner highlight — top left lobe
            hl_x = cx - r * 0.28
            hl_y = cy + r * 0.38
            Color(1.0, 1.0, 1.0, 0.18)
            Ellipse(pos=(hl_x - r*0.22, hl_y - r*0.14), size=(r*0.44, r*0.28))

            # Aorta nub at top centre
            Color(0.55, 0.15, 0.80, 0.7)
            Ellipse(pos=(cx - r*0.12, cy + r*0.62), size=(r*0.24, r*0.32))

            # ECG blip line across bottom of heart
            ecg_y = cy - r * 0.72
            ecg_pts = [
                cx - r*0.8, ecg_y,
                cx - r*0.4, ecg_y,
                cx - r*0.25, ecg_y + r*0.28,
                cx - r*0.1,  ecg_y - r*0.38,
                cx + r*0.05, ecg_y + r*0.52,
                cx + r*0.18, ecg_y,
                cx + r*0.8,  ecg_y,
            ]
            Color(0.91, 0.475, 0.976, 0.55)
            Line(points=ecg_pts, width=dp(1.2))

    def stop(self):
        if self._pulse_event:
            self._pulse_event.cancel()
            self._pulse_event = None


# ── BPM Graph ──────────────────────────────────────────────────────────────────

class BPMGraph(Widget):
    history = ListProperty([])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, history=self._draw)

    def push(self, bpm):
        h = list(self.history)[-59:]
        h.append(bpm)
        self.history = h

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*CARD_BG)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        if len(self.history) < 2:
            return
        pts = self.history
        mn, mx = min(pts), max(pts)
        rng = max(mx - mn, 20)
        w, h   = self.size
        px, py = self.pos
        pad = dp(10)
        uw  = (w - 2*pad) / (len(pts) - 1)
        points = []
        for i, v in enumerate(pts):
            x = px + pad + i * uw
            y = py + pad + ((v - mn) / rng) * (h - 2*pad)
            points += [x, y]
        with self.canvas:
            # Fill
            fill_v = [points[0], py + pad, 0, 0]
            for i in range(0, len(points), 2):
                fill_v += [points[i], points[i+1], 0, 0]
            fill_v += [points[-2], py + pad, 0, 0]
            Color(*ACCENT[:3], 0.22)
            Mesh(vertices=fill_v, indices=list(range(len(fill_v)//4)), mode='triangle_fan')
            # Line
            Color(*ACCENT, 0.9)
            Line(points=points, width=dp(1.8))
            # Live dot
            Color(*STATUS_FUCH)
            r = dp(4)
            Ellipse(pos=(points[-2]-r, points[-1]-r), size=(r*2, r*2))


# ── HRV Bar Chart (weekly summary) ────────────────────────────────────────────

class HRVBarChart(Widget):
    data = ListProperty([])   # list of (label, value) tuples

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, data=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        if not self.data:
            return
        n   = len(self.data)
        w, h = self.size
        px, py = self.pos
        pad  = dp(8)
        gap  = dp(6)
        bar_w = (w - 2*pad - gap*(n-1)) / n
        max_v = max(v for _, v in self.data) or 1
        with self.canvas:
            for i, (label, val) in enumerate(self.data):
                bx = px + pad + i * (bar_w + gap)
                bar_h = (val / max_v) * (h - dp(32))
                by = py + dp(22)
                # Bar background
                Color(*PILL_BG)
                RoundedRectangle(pos=(bx, by), size=(bar_w, h - dp(22)), radius=[dp(4)])
                # Bar fill — colour by value
                ratio = val / max_v
                r = 0.49 + ratio * 0.42
                g = 0.27 + ratio * 0.08
                b = 0.93 - ratio * 0.3
                Color(r, g, b, 0.9)
                RoundedRectangle(pos=(bx, by), size=(bar_w, bar_h), radius=[dp(4)])
                # Label
                Color(*TEXT_MUTED)
                # We just use the bar positions — labels are in a separate layout

# ── Shared widgets ─────────────────────────────────────────────────────────────

class PurpleButton(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", [0, 0, 0, 0])
        kw.setdefault("color", TEXT_MAIN)
        kw.setdefault("font_size", sp(16))
        kw.setdefault("bold", True)
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(54))
        super().__init__(**kw)
        with self.canvas.before:
            self._col  = Color(*ACCENT)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(27)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._rect.pos  = self.pos
        self._rect.size = self.size

    def on_press(self):   self._col.rgba = list(ACCENT2)
    def on_release(self): self._col.rgba = list(ACCENT)


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
    def __init__(self, value="--", label="", **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*PILL_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._upd, size=self._upd)
        self.val_lbl = Label(
            text=str(value), font_size=sp(22), bold=True, color=TEXT_MAIN,
            size_hint=(1, None), height=dp(34),
            pos_hint={"center_x": 0.5, "top": 0.75},
        )
        self.lbl = Label(
            text=label, font_size=sp(11), color=TEXT_MUTED,
            size_hint=(1, None), height=dp(18),
            pos_hint={"center_x": 0.5, "top": 0.38},
        )
        self.add_widget(self.val_lbl)
        self.add_widget(self.lbl)

    def _upd(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size

    def set_value(self, v, color=None):
        self.val_lbl.text = str(v)
        if color:
            self.val_lbl.color = color


class StepDots(BoxLayout):
    def __init__(self, total=3, current=1, **kw):
        kw.setdefault("orientation", "horizontal")
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (dp(72), dp(12)))
        kw.setdefault("spacing", dp(8))
        super().__init__(**kw)
        for i in range(1, total+1):
            w = Widget(size_hint=(None, None), size=(dp(10), dp(10)))
            c = list(ACCENT) if i == current else list(TEXT_MUTED)
            with w.canvas:
                Color(*c)
                Ellipse(pos=(0, 0), size=(dp(10), dp(10)))
            self.add_widget(w)


class StepBadge(Label):
    def __init__(self, **kw):
        kw.setdefault("font_size", sp(12))
        kw.setdefault("color", TEXT_MUTED)
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (dp(110), dp(26)))
        super().__init__(**kw)
        self._draw_bg()
        self.bind(pos=lambda *_: self._draw_bg(), size=lambda *_: self._draw_bg())

    def _draw_bg(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PILL_BG)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(13)])


# ── Onboarding screens ─────────────────────────────────────────────────────────

def _screen_bg(root):
    with root.canvas.before:
        Color(*BG)
        bg = Rectangle(pos=root.pos, size=root.size)
    root.bind(
        pos=lambda *_: setattr(bg, "pos", root.pos),
        size=lambda *_: setattr(bg, "size", root.size),
    )


class OnboardScreen1(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(64), dp(32), dp(40)],
            spacing=dp(0), size_hint=(1, 1),
        )

        bw = BoxLayout(size_hint_y=None, height=dp(38))
        bw.add_widget(StepBadge(text="  step 1 of 3  "))
        bw.add_widget(Widget())
        col.add_widget(bw)
        col.add_widget(Widget(size_hint_y=None, height=dp(36)))

        t = Label(text="what's your name?", font_size=sp(30), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(44), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(t)
        col.add_widget(Widget(size_hint_y=None, height=dp(8)))
        s = Label(text="so we can make this feel like yours",
                  font_size=sp(15), color=TEXT_MUTED,
                  size_hint_y=None, height=dp(26), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(s)
        col.add_widget(Widget(size_hint_y=None, height=dp(40)))

        self.name_input = TextInput(
            hint_text="your name", hint_text_color=TEXT_MUTED,
            foreground_color=TEXT_MAIN, background_color=PILL_BG,
            cursor_color=ACCENT, font_size=sp(18),
            size_hint_y=None, height=dp(56),
            padding=[dp(18), dp(16), dp(18), dp(16)], multiline=False,
        )
        col.add_widget(self.name_input)
        col.add_widget(Widget())

        btn = PurpleButton(text="continue")
        btn.bind(on_release=self._next)
        col.add_widget(btn)
        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        dr = BoxLayout(size_hint_y=None, height=dp(16))
        dr.add_widget(Widget())
        dr.add_widget(StepDots(total=3, current=1))
        dr.add_widget(Widget())
        col.add_widget(dr)

        root.add_widget(col)
        self.add_widget(root)

    def _next(self, *_):
        name = self.name_input.text.strip() or "friend"
        App.get_running_app().profile["name"] = name
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard2"


class OnboardScreen2(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)
        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(64), dp(32), dp(40)],
            spacing=dp(0), size_hint=(1, 1),
        )
        bw = BoxLayout(size_hint_y=None, height=dp(38))
        bw.add_widget(StepBadge(text="  step 2 of 3  "))
        bw.add_widget(Widget())
        col.add_widget(bw)
        col.add_widget(Widget(size_hint_y=None, height=dp(28)))
        t = Label(text="your resting heart rate", font_size=sp(28), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(44), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(t)
        col.add_widget(Widget(size_hint_y=None, height=dp(6)))
        s = Label(text="used to detect spikes accurately",
                  font_size=sp(15), color=TEXT_MUTED,
                  size_hint_y=None, height=dp(26), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(s)
        col.add_widget(Widget(size_hint_y=None, height=dp(28)))

        boxes = GridLayout(cols=2, spacing=dp(12), size_hint_y=None, height=dp(88))
        self.box_resting   = StatBox(value="65",  label="resting BPM")
        self.box_threshold = StatBox(value="110", label="alert threshold")
        boxes.add_widget(self.box_resting)
        boxes.add_widget(self.box_threshold)
        col.add_widget(boxes)
        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.slider = Slider(min=40, max=100, value=65,
                             size_hint_y=None, height=dp(44),
                             cursor_size=(dp(28), dp(28)))
        self.slider.bind(value=self._slide)
        col.add_widget(self.slider)
        d = Label(text="drag to set your resting BPM", font_size=sp(13),
                  color=TEXT_MUTED, size_hint_y=None, height=dp(22))
        col.add_widget(d)
        col.add_widget(Widget())

        btn = PurpleButton(text="continue")
        btn.bind(on_release=self._next)
        col.add_widget(btn)
        col.add_widget(Widget(size_hint_y=None, height=dp(4)))
        ghost = GhostButton(text="use defaults")
        ghost.bind(on_release=self._defaults)
        col.add_widget(ghost)
        col.add_widget(Widget(size_hint_y=None, height=dp(14)))
        dr = BoxLayout(size_hint_y=None, height=dp(16))
        dr.add_widget(Widget())
        dr.add_widget(StepDots(total=3, current=2))
        dr.add_widget(Widget())
        col.add_widget(dr)

        root.add_widget(col)
        self.add_widget(root)

    def _slide(self, _, val):
        r = int(val)
        self.box_resting.set_value(str(r))
        self.box_threshold.set_value(str(r + 45))

    def _next(self, *_):
        p = App.get_running_app().profile
        p["resting_bpm"] = int(self.slider.value)
        p["threshold"]   = int(self.slider.value) + 45
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard3"

    def _defaults(self, *_):
        p = App.get_running_app().profile
        p["resting_bpm"] = 65
        p["threshold"]   = 110
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard3"


class OnboardScreen3(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)
        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(64), dp(32), dp(40)],
            spacing=dp(0), size_hint=(1, 1),
        )
        bw = BoxLayout(size_hint_y=None, height=dp(38))
        bw.add_widget(StepBadge(text="  step 3 of 3  "))
        bw.add_widget(Widget())
        col.add_widget(bw)
        col.add_widget(Widget(size_hint_y=None, height=dp(28)))
        t = Label(text="spike sensitivity", font_size=sp(30), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(44), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(t)
        col.add_widget(Widget(size_hint_y=None, height=dp(6)))
        s = Label(text="alert me when HR rises by...",
                  font_size=sp(15), color=TEXT_MUTED,
                  size_hint_y=None, height=dp(26), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(s)
        col.add_widget(Widget(size_hint_y=None, height=dp(28)))

        boxes = GridLayout(cols=2, spacing=dp(12), size_hint_y=None, height=dp(88))
        self.box_delta = StatBox(value="+30", label="BPM spike delta")
        self.box_dur   = StatBox(value="10s", label="sustained duration")
        boxes.add_widget(self.box_delta)
        boxes.add_widget(self.box_dur)
        col.add_widget(boxes)
        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.slider = Slider(min=15, max=50, value=30,
                             size_hint_y=None, height=dp(44),
                             cursor_size=(dp(28), dp(28)))
        self.slider.bind(value=lambda _, v: self.box_delta.set_value(f"+{int(v)}"))
        col.add_widget(self.slider)
        d = Label(text="matches typical POTS thresholds", font_size=sp(13),
                  color=TEXT_MUTED, size_hint_y=None, height=dp(22))
        col.add_widget(d)
        col.add_widget(Widget())

        btn = PurpleButton(text="let's go")
        btn.bind(on_release=self._finish)
        col.add_widget(btn)
        col.add_widget(Widget(size_hint_y=None, height=dp(20)))
        dr = BoxLayout(size_hint_y=None, height=dp(16))
        dr.add_widget(Widget())
        dr.add_widget(StepDots(total=3, current=3))
        dr.add_widget(Widget())
        col.add_widget(dr)

        root.add_widget(col)
        self.add_widget(root)

    def _finish(self, *_):
        p = App.get_running_app().profile
        p["spike_delta"]    = int(self.slider.value)
        p["spike_duration"] = 10
        p["vibration"]      = True
        p["sound_alerts"]   = True
        save_profile(p)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "monitor"
        App.get_running_app().root.get_screen("monitor").start_monitoring()


# ── Monitor screen ─────────────────────────────────────────────────────────────

class MonitorScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._worker       = None
        self._alert_engine = None
        self._dev_taps     = []
        self._alert_up     = False
        self._build()

    def _build(self):
        root = FloatLayout()
        _screen_bg(root)

        # Heart background — large, centered, behind everything
        self.heart = HeartWidget(
            size_hint=(None, None), size=(dp(260), dp(260)),
            pos_hint={"center_x": 0.5, "center_y": 0.62},
            opacity=0.35,
        )
        root.add_widget(self.heart)

        # Main content column (on top of heart)
        col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(52), dp(24), dp(24)],
            spacing=dp(12), size_hint=(1, 1),
        )

        # ── Top row: greeting + avatar button ──
        top = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.greeting_lbl = Label(
            text="good morning", font_size=sp(18), bold=True,
            color=TEXT_MAIN, halign="left", valign="middle",
        )
        self.greeting_lbl.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        top.add_widget(self.greeting_lbl)

        self.initial_btn = Button(
            size_hint=(None, None), size=(dp(40), dp(40)),
            background_normal="", background_color=[0, 0, 0, 0],
        )
        with self.initial_btn.canvas.before:
            Color(*ACCENT)
            self._circle = Ellipse(
                pos=self.initial_btn.pos, size=self.initial_btn.size
            )
        self.initial_btn.bind(
            pos=lambda *_: setattr(self._circle, "pos", self.initial_btn.pos),
            size=lambda *_: setattr(self._circle, "size", self.initial_btn.size),
            on_release=self._initial_tapped,
        )
        self.initial_lbl = Label(
            text="?", font_size=sp(16), bold=True, color=TEXT_MAIN,
            size_hint=(None, None), size=(dp(40), dp(40)),
        )
        top.add_widget(self.initial_btn)
        top.add_widget(self.initial_lbl)
        col.add_widget(top)

        # ── Status ──
        self.status_lbl = Label(
            text="not connected", font_size=sp(13),
            color=TEXT_MUTED, size_hint_y=None, height=dp(20), halign="left",
        )
        self.status_lbl.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        col.add_widget(self.status_lbl)

        # ── Big BPM number (sits on top of heart) ──
        bpm_box = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(110), spacing=dp(0)
        )
        self.bpm_lbl = Label(
            text="--", font_size=sp(96), bold=True,
            color=BPM_REST, size_hint_y=None, height=dp(94),
        )
        bpm_unit = Label(
            text="BPM", font_size=sp(13), color=TEXT_MUTED,
            size_hint_y=None, height=dp(16),
        )
        bpm_box.add_widget(self.bpm_lbl)
        bpm_box.add_widget(bpm_unit)
        col.add_widget(bpm_box)

        # ── HRV ──
        self.hrv_lbl = Label(
            text="HRV  --  ms", font_size=sp(15),
            color=TEXT_MAIN, size_hint_y=None, height=dp(22),
        )
        col.add_widget(self.hrv_lbl)

        # ── Graph ──
        self.graph = BPMGraph(size_hint_y=None, height=dp(80))
        col.add_widget(self.graph)

        # ── Time labels under graph ──
        tlrow = BoxLayout(size_hint_y=None, height=dp(16))
        for t in ["0s", "15s", "30s", "45s", "60s"]:
            tlrow.add_widget(Label(text=t, font_size=sp(10), color=TEXT_MUTED))
        col.add_widget(tlrow)

        # ── Stat boxes ──
        stats = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(80))
        self.stat_resting = StatBox(value="--",    label="resting")
        self.stat_hrv     = StatBox(value="--",    label="HRV ms")
        self.stat_status  = StatBox(value="clear", label="status")
        self.stat_status.val_lbl.color = list(STATUS_GRN)
        stats.add_widget(self.stat_resting)
        stats.add_widget(self.stat_hrv)
        stats.add_widget(self.stat_status)
        col.add_widget(stats)

        col.add_widget(Widget())

        # ── Bottom nav bar ──
        nav = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        self.connect_btn = PurpleButton(text="connect to band")
        self.connect_btn.bind(on_release=self._connect_pressed)

        summary_btn = Button(
            text="weekly", font_size=sp(13),
            background_normal="", background_color=[0, 0, 0, 0],
            color=TEXT_MUTED, size_hint=(None, 1), width=dp(70),
        )
        summary_btn.bind(on_release=lambda *_: self._go_summary())

        nav.add_widget(self.connect_btn)
        nav.add_widget(summary_btn)
        col.add_widget(nav)

        root.add_widget(col)

        # ── Alert card ──
        self._alert_card = self._make_alert_card()
        root.add_widget(self._alert_card)

        self.add_widget(root)
        self._root_fl = root

    def _make_alert_card(self):
        card = FloatLayout(size_hint=(1, None), height=dp(170))
        card.y = -dp(200)

        with card.canvas.before:
            Color(*CARD_BG)
            self._card_bg = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[dp(20), dp(20), 0, 0]
            )
            Color(*ACCENT, 0.45)
            self._card_border = Line(
                rounded_rectangle=[card.x, card.y, card.width, card.height, dp(20)],
                width=dp(1.2),
            )

        def upd(*_):
            self._card_bg.pos  = card.pos
            self._card_bg.size = card.size
            self._card_border.rounded_rectangle = [
                card.x, card.y, card.width, card.height, dp(20)
            ]
        card.bind(pos=upd, size=upd)

        inner = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(18), dp(24), dp(14)],
            spacing=dp(8), size_hint=(1, 1),
        )
        self.alert_title = Label(
            text="spike detected", font_size=sp(17), bold=True,
            color=TEXT_MAIN, halign="left", size_hint_y=None, height=dp(28),
        )
        self.alert_title.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        self.alert_msg = Label(
            text="", font_size=sp(13), color=TEXT_MUTED,
            halign="left", size_hint_y=None, height=dp(38),
        )
        self.alert_msg.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, dp(38)))
        )
        dismiss = PurpleButton(text="ok - resting now", height=dp(44))
        dismiss.bind(on_release=self._dismiss_alert)
        inner.add_widget(self.alert_title)
        inner.add_widget(self.alert_msg)
        inner.add_widget(dismiss)
        card.add_widget(inner)
        return card

    def on_enter(self):
        self._refresh_profile()

    def _refresh_profile(self):
        p    = App.get_running_app().profile
        name = p.get("name", "friend")
        self.greeting_lbl.text = greeting(name)
        self.initial_lbl.text  = name[0].upper() if name else "?"
        self.stat_resting.set_value(str(p.get("resting_bpm", 65)))

    def start_monitoring(self):
        self._refresh_profile()
        p = App.get_running_app().profile
        from alert_engine import AlertEngine, AlertConfig
        self._alert_engine = AlertEngine(AlertConfig(
            sustained_hr_threshold=p.get("threshold", 110),
            sustained_duration_secs=p.get("spike_duration", 10),
            spike_bpm_delta=p.get("spike_delta", 30),
        ))
        if USE_SIMULATOR:
            self._start_sim("resting")
        else:
            self._start_ble()

    def _start_sim(self, scenario="resting"):
        if self._worker:
            self._worker.stop()
        from fake_ble import FakeBLEWorker
        self._worker = FakeBLEWorker(
            on_bpm=self._on_bpm,
            on_status=self._on_status,
            on_alert=self._on_alert_event,
            scenario=scenario,
        )
        self._worker.start()

    def _start_ble(self):
        if self._worker:
            self._worker.stop()
        try:
            import threading
            threading.Thread(target=self._ble_thread, daemon=True).start()
        except Exception as e:
            Clock.schedule_once(
                lambda dt: setattr(self.status_lbl, "text", f"BLE error: {e}"), 0
            )

    def _ble_thread(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._ble_main())

    async def _ble_main(self):
        from bleak import BleakScanner, BleakClient
        Clock.schedule_once(lambda dt: setattr(
            self.status_lbl, "text", "scanning for band..."), 0)
        devices  = await BleakScanner.discover(timeout=30.0)
        keywords = ["mi band", "xiaomi", "band 10", "smart band", "miband"]
        address  = None
        for d in devices:
            if d.name and any(k in d.name.lower() for k in keywords):
                address = d.address
                Clock.schedule_once(lambda dt: setattr(
                    self.status_lbl, "text", f"found: {d.name}"), 0)
                break
        if not address:
            Clock.schedule_once(lambda dt: setattr(
                self.status_lbl, "text", "band not found — close Mi Fitness app"), 0)
            return
        try:
            async with BleakClient(address, timeout=20.0) as client:
                Clock.schedule_once(lambda dt: setattr(
                    self.status_lbl, "text", "connected — monitoring"), 0)
                HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
                await client.start_notify(HR_UUID, self._ble_handler)
                while client.is_connected:
                    await asyncio.sleep(0.5)
                await client.stop_notify(HR_UUID)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(
                self.status_lbl, "text", f"error: {e}"), 0)

    def _ble_handler(self, sender, data):
        flags = data[0]
        bpm   = int.from_bytes(data[1:3], "little") if (flags & 1) else data[1]
        Clock.schedule_once(lambda dt: self._on_bpm(bpm, None), 0)

    def _on_bpm(self, bpm, rmssd):
        p         = App.get_running_app().profile
        resting   = p.get("resting_bpm", 65)
        threshold = p.get("threshold", 110)

        self.bpm_lbl.text = str(bpm)
        Animation(color=bpm_colour(bpm, resting, threshold), duration=0.4).start(self.bpm_lbl)

        # Update heart animation speed
        self.heart.set_bpm(bpm)

        if rmssd is not None:
            self.hrv_lbl.text = f"HRV  {int(rmssd)}  ms"
            self.stat_hrv.set_value(str(int(rmssd)))

        self.graph.push(bpm)

        if bpm >= threshold:
            self.stat_status.set_value("alert",      list(STATUS_RED))
        elif bpm >= resting + 20:
            self.stat_status.set_value("recovering", list(STATUS_FUCH))
        else:
            self.stat_status.set_value("clear",       list(STATUS_GRN))

        # Log data point
        append_log({
            "ts":    datetime.now().isoformat(),
            "bpm":   bpm,
            "rmssd": int(rmssd) if rmssd else None,
        })

        # Alert engine check
        if self._alert_engine and not self._alert_up:
            result = self._alert_engine.update(bpm)
            if result:
                self._show_alert(result.type, result.message)

    def _on_status(self, status):
        self.status_lbl.text = status

    def _on_alert_event(self, alert_event):
        if not self._alert_up:
            self._show_alert(alert_event.type, alert_event.message)

    def _show_alert(self, atype, msg):
        self._alert_up = True
        self.alert_title.text = "spike detected" if atype == "spike" else "sustained HR"
        self.alert_msg.text   = msg
        Animation(y=dp(0), duration=0.35, t="out_back").start(self._alert_card)
        try:
            from plyer import vibrator
            vibrator.vibrate(time=1.5)
        except Exception:
            pass

    def _dismiss_alert(self, *_):
        def _done(*_):
            self._alert_up = False
            if self._alert_engine:
                self._alert_engine._spike_alerted     = False
                self._alert_engine._sustained_alerted = False
                self._alert_engine._sustained_start   = None
        anim = Animation(y=-dp(200), duration=0.25, t="in_quad")
        anim.bind(on_complete=_done)
        anim.start(self._alert_card)

    def _connect_pressed(self, *_):
        self.connect_btn.text     = "connecting..."
        self.connect_btn.disabled = True
        Clock.schedule_once(lambda dt: self.start_monitoring(), 0.1)

    def _go_summary(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "summary"

    def _initial_tapped(self, *_):
        now = time.time()
        self._dev_taps = [t for t in self._dev_taps if now - t < 1.5]
        self._dev_taps.append(now)
        if len(self._dev_taps) >= 5:
            self._dev_taps = []
            self._open_dev_mode()
        else:
            if len(self._dev_taps) == 1:
                Clock.schedule_once(self._single_tap_nav, 1.6)

    def _single_tap_nav(self, *_):
        if len(self._dev_taps) < 5:
            self._dev_taps = []
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = "settings"

    def _open_dev_mode(self):
        content = BoxLayout(orientation="vertical", padding=[dp(20), dp(20)], spacing=dp(12))
        with content.canvas.before:
            Color(*CARD_BG)
            bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(
            pos=lambda *_: setattr(bg, "pos", content.pos),
            size=lambda *_: setattr(bg, "size", content.size),
        )
        content.add_widget(Label(
            text="developer mode", font_size=sp(16), bold=True,
            color=TEXT_MAIN, size_hint_y=None, height=dp(30),
        ))
        self._dev_input = TextInput(
            hint_text="enter code", hint_text_color=TEXT_MUTED,
            foreground_color=TEXT_MAIN, background_color=PILL_BG,
            cursor_color=ACCENT, font_size=sp(16),
            size_hint_y=None, height=dp(48),
            multiline=False, password=True,
        )
        self._dev_err = Label(text="", font_size=sp(13), color=STATUS_RED,
                              size_hint_y=None, height=dp(22))
        ok = PurpleButton(text="unlock")
        ok.bind(on_release=self._check_code)
        content.add_widget(self._dev_input)
        content.add_widget(self._dev_err)
        content.add_widget(ok)
        self._dev_popup = Popup(
            title="", content=content,
            size_hint=(0.85, None), height=dp(240),
            background_color=CARD_BG, separator_height=0, title_size=0,
        )
        self._dev_popup.open()

    def _check_code(self, *_):
        if self._dev_input.text.strip() == DEV_CODE:
            self._dev_popup.dismiss()
            self._open_scenario_picker()
        else:
            self._dev_input.text = ""
            self._dev_err.text   = "wrong code - try again"

    def _open_scenario_picker(self):
        content = BoxLayout(orientation="vertical", padding=[dp(16), dp(16)], spacing=dp(8))
        with content.canvas.before:
            Color(*CARD_BG)
            bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(
            pos=lambda *_: setattr(bg, "pos", content.pos),
            size=lambda *_: setattr(bg, "size", content.size),
        )
        content.add_widget(Label(
            text="select scenario", font_size=sp(16), bold=True,
            color=TEXT_MAIN, size_hint_y=None, height=dp(30),
        ))

        # Simulator toggle
        sim_row = BoxLayout(size_hint_y=None, height=dp(40))
        sim_lbl = Label(
            text=f"simulator: {'ON' if USE_SIMULATOR else 'OFF'}",
            font_size=sp(14), color=STATUS_GRN if USE_SIMULATOR else STATUS_RED,
        )
        sim_toggle = GhostButton(
            text="toggle",
            size_hint=(None, 1), width=dp(80),
        )
        def _toggle_sim(*_):
            global USE_SIMULATOR
            USE_SIMULATOR = not USE_SIMULATOR
            sim_lbl.text = f"simulator: {'ON' if USE_SIMULATOR else 'OFF'}"
            sim_lbl.color = STATUS_GRN if USE_SIMULATOR else STATUS_RED
        sim_toggle.bind(on_release=_toggle_sim)
        sim_row.add_widget(sim_lbl)
        sim_row.add_widget(sim_toggle)
        content.add_widget(sim_row)

        self._sc_popup = Popup(
            title="", content=content,
            size_hint=(0.85, None), height=dp(420),
            background_color=CARD_BG, separator_height=0, title_size=0,
        )
        for sc in SCENARIOS:
            btn = PurpleButton(text=sc, height=dp(42))
            btn._sc = sc
            btn.bind(on_release=self._pick_scenario)
            content.add_widget(btn)
        cancel = GhostButton(text="cancel")
        cancel.bind(on_release=self._sc_popup.dismiss)
        content.add_widget(cancel)
        self._sc_popup.open()

    def _pick_scenario(self, btn):
        self._sc_popup.dismiss()
        self._alert_up = False
        Animation(y=-dp(200), duration=0.1).start(self._alert_card)
        self._start_sim(btn._sc)


# ── Weekly Summary Screen ──────────────────────────────────────────────────────

class SummaryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)

        sv = ScrollView(size_hint=(1, 1))
        self._col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(56), dp(24), dp(32)],
            spacing=dp(16), size_hint_y=None,
        )
        self._col.bind(minimum_height=self._col.setter("height"))
        sv.add_widget(self._col)
        root.add_widget(sv)
        self.add_widget(root)

    def on_enter(self):
        self._col.clear_widgets()
        self._build_content()

    def _build_content(self):
        col = self._col
        p   = App.get_running_app().profile
        name = p.get("name", "friend")

        # Back button
        back_row = BoxLayout(size_hint_y=None, height=dp(40))
        back = GhostButton(text="< back", size_hint=(None, 1), width=dp(80))
        back.bind(on_release=lambda *_: self._back())
        back_row.add_widget(back)
        back_row.add_widget(Widget())
        col.add_widget(back_row)

        # Title
        t = Label(text=f"hi, {name}!", font_size=sp(26), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(38), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(t)
        s = Label(text="here's your weekly summary",
                  font_size=sp(15), color=TEXT_MUTED,
                  size_hint_y=None, height=dp(24), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(s)

        # Compute weekly stats from log
        stats = self._compute_weekly_stats()

        # Big avg BPM card
        avg_card = FloatLayout(size_hint_y=None, height=dp(100))
        with avg_card.canvas.before:
            Color(*PILL_BG)
            bg = RoundedRectangle(pos=avg_card.pos, size=avg_card.size, radius=[dp(16)])
        avg_card.bind(
            pos=lambda *_: setattr(bg, "pos", avg_card.pos),
            size=lambda *_: setattr(bg, "size", avg_card.size),
        )
        avg_bpm_lbl = Label(
            text=str(stats["avg_bpm"]),
            font_size=sp(52), bold=True, color=BPM_ELEV,
            size_hint=(None, None), size=(dp(120), dp(70)),
            pos_hint={"x": 0.05, "center_y": 0.55},
        )
        avg_card.add_widget(avg_bpm_lbl)
        avg_card.add_widget(Label(
            text="bmp", font_size=sp(14), color=TEXT_MUTED,
            size_hint=(None, None), size=(dp(40), dp(24)),
            pos_hint={"x": 0.38, "center_y": 0.38},
        ))
        avg_card.add_widget(Label(
            text=f"{stats['max_bpm']}  Max   {stats['min_bpm']}  Min",
            font_size=sp(13), color=TEXT_MUTED,
            size_hint=(None, None), size=(dp(160), dp(24)),
            pos_hint={"right": 0.97, "center_y": 0.5},
        ))
        col.add_widget(avg_card)

        # HRV section
        hrv_title = Label(text="Heart Rate Variability",
                          font_size=sp(15), bold=True, color=TEXT_MAIN,
                          size_hint_y=None, height=dp(28), halign="left")
        hrv_title.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(hrv_title)

        hrv_row = BoxLayout(size_hint_y=None, height=dp(36))
        hrv_row.add_widget(Label(
            text="Heart Rate Variability",
            font_size=sp(13), color=TEXT_MUTED, halign="left",
        ))
        hrv_row.add_widget(Label(
            text=f"{stats['avg_hrv']} ms",
            font_size=sp(18), bold=True, color=STATUS_FUCH,
            halign="right",
        ))
        col.add_widget(hrv_row)

        # HRV bar chart for last 7 days
        hrv_card = BoxLayout(orientation="vertical",
                             size_hint_y=None, height=dp(160),
                             padding=[dp(12), dp(12)])
        with hrv_card.canvas.before:
            Color(*PILL_BG)
            hbg = RoundedRectangle(pos=hrv_card.pos, size=hrv_card.size, radius=[dp(14)])
        hrv_card.bind(
            pos=lambda *_: setattr(hbg, "pos", hrv_card.pos),
            size=lambda *_: setattr(hbg, "size", hrv_card.size),
        )

        chart = HRVBarChart(size_hint_y=1)
        chart.data = stats["daily_hrv"]
        hrv_card.add_widget(chart)

        # Day labels under chart
        day_row = BoxLayout(size_hint_y=None, height=dp(20))
        for label, _ in stats["daily_hrv"]:
            day_row.add_widget(Label(
                text=label, font_size=sp(10), color=TEXT_MUTED,
            ))
        hrv_card.add_widget(day_row)
        col.add_widget(hrv_card)

        # Two stat boxes row
        row2 = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(90))
        stress_box = StatBox(value=stats["stress_label"], label="Stress Level")
        stress_box.val_lbl.color = (
            list(STATUS_GRN)  if stats["stress_label"] == "Low" else
            list(AMBER)       if stats["stress_label"] == "Med" else
            list(STATUS_RED)
        )
        avg_hrv_box = StatBox(value=f"{stats['avg_hrv']} ms", label="Ave. Variability")
        row2.add_widget(stress_box)
        row2.add_widget(avg_hrv_box)
        col.add_widget(row2)

        # Spike count
        spikes_row = BoxLayout(size_hint_y=None, height=dp(56),
                               padding=[dp(16), dp(8)])
        with spikes_row.canvas.before:
            Color(*PILL_BG)
            sbg = RoundedRectangle(pos=spikes_row.pos, size=spikes_row.size, radius=[dp(12)])
        spikes_row.bind(
            pos=lambda *_: setattr(sbg, "pos", spikes_row.pos),
            size=lambda *_: setattr(sbg, "size", spikes_row.size),
        )
        spike_icon = Label(text="!", font_size=sp(18), bold=True,
                           color=AMBER, size_hint=(None, 1), width=dp(30))
        spike_msg = Label(
            text=f"You had {stats['spike_count']} spike events this week",
            font_size=sp(13), color=TEXT_MUTED, halign="left", valign="middle",
        )
        spike_msg.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        spikes_row.add_widget(spike_icon)
        spikes_row.add_widget(spike_msg)
        col.add_widget(spikes_row)

        # Insight card
        insight_card = BoxLayout(orientation="vertical",
                                 size_hint_y=None, height=dp(80),
                                 padding=[dp(16), dp(12)])
        with insight_card.canvas.before:
            Color(0.2, 0.08, 0.35, 1)
            ibg = RoundedRectangle(pos=insight_card.pos,
                                   size=insight_card.size, radius=[dp(12)])
        insight_card.bind(
            pos=lambda *_: setattr(ibg, "pos", insight_card.pos),
            size=lambda *_: setattr(ibg, "size", insight_card.size),
        )
        insight_text = self._get_insight(stats)
        insight_lbl = Label(
            text=insight_text,
            font_size=sp(13), color=TEXT_MAIN,
            halign="left", valign="middle",
        )
        insight_lbl.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        insight_card.add_widget(insight_lbl)
        col.add_widget(insight_card)

        col.add_widget(Widget(size_hint_y=None, height=dp(16)))

    def _compute_weekly_stats(self):
        log = load_log()
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        week_entries = []
        for e in log:
            try:
                ts = datetime.fromisoformat(e["ts"])
                if ts >= week_ago:
                    week_entries.append(e)
            except Exception:
                pass

        bpms  = [e["bpm"] for e in week_entries if e.get("bpm")]
        hrvs  = [e["rmssd"] for e in week_entries if e.get("rmssd")]
        # Count spikes as entries where bpm > threshold
        p = App.get_running_app().profile
        thresh = p.get("threshold", 110)
        spikes = sum(1 for b in bpms if b >= thresh)

        avg_bpm = round(sum(bpms)/len(bpms)) if bpms else 0
        max_bpm = max(bpms) if bpms else 0
        min_bpm = min(bpms) if bpms else 0
        avg_hrv = round(sum(hrvs)/len(hrvs)) if hrvs else 0

        # Daily HRV for last 7 days
        days = []
        for i in range(6, -1, -1):
            d = now - timedelta(days=i)
            day_label = d.strftime("%a")
            day_hrvs = []
            for e in log:
                try:
                    ts = datetime.fromisoformat(e["ts"])
                    if ts.date() == d.date() and e.get("rmssd"):
                        day_hrvs.append(e["rmssd"])
                except Exception:
                    pass
            daily_avg = round(sum(day_hrvs)/len(day_hrvs)) if day_hrvs else 0
            days.append((day_label, daily_avg))

        # Stress label based on HRV
        if avg_hrv >= 50:
            stress = "Low"
        elif avg_hrv >= 25:
            stress = "Med"
        else:
            stress = "High"

        return {
            "avg_bpm":     avg_bpm or "--",
            "max_bpm":     max_bpm or "--",
            "min_bpm":     min_bpm or "--",
            "avg_hrv":     avg_hrv or "--",
            "spike_count": spikes,
            "daily_hrv":   days,
            "stress_label": stress,
        }

    def _get_insight(self, stats):
        hrv = stats["avg_hrv"]
        if hrv == "--":
            return "Start monitoring to see weekly insights here."
        try:
            hrv = int(hrv)
        except Exception:
            return "Keep monitoring to build up your insights."
        if hrv >= 50:
            return "Your HRV is above average for your age group — your autonomic nervous system is recovering well."
        elif hrv >= 25:
            return "Your HRV is in a moderate range. Consistent rest and hydration help improve POTS symptoms."
        else:
            return "Your HRV is lower than ideal this week. Prioritise rest, salt intake, and avoid prolonged standing."

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "monitor"


# ── Settings screen ────────────────────────────────────────────────────────────

class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(52), dp(24), dp(30)],
            spacing=dp(0), size_hint=(1, 1),
        )

        back_row = BoxLayout(size_hint_y=None, height=dp(40))
        back_btn = GhostButton(text="back", size_hint=(None, 1), width=dp(70))
        back_btn.bind(on_release=self._back)
        back_row.add_widget(back_btn)
        back_row.add_widget(Widget())
        col.add_widget(back_row)

        col.add_widget(Widget(size_hint_y=None, height=dp(10)))

        h = Label(text="profile", font_size=sp(26), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(40), halign="left")
        h.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(h)
        col.add_widget(Widget(size_hint_y=None, height=dp(16)))

        self._rows = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self._rows.bind(minimum_height=self._rows.setter("height"))
        col.add_widget(self._rows)

        col.add_widget(Widget())

        back2 = PurpleButton(text="back to monitor")
        back2.bind(on_release=self._back)
        col.add_widget(back2)

        root.add_widget(col)
        self.add_widget(root)

    def on_enter(self):
        p = App.get_running_app().profile
        self._rows.clear_widgets()
        for lbl, val in [
            ("name",            p.get("name", "--")),
            ("resting BPM",     str(p.get("resting_bpm", 65))),
            ("alert threshold", str(p.get("threshold", 110))),
            ("spike delta",     f"+{p.get('spike_delta', 30)}"),
            ("simulator",       "on" if USE_SIMULATOR else "off"),
            ("vibration",       "on" if p.get("vibration", True) else "off"),
        ]:
            row = BoxLayout(size_hint_y=None, height=dp(50),
                            padding=[dp(16), 0, dp(16), 0])
            _pill_bg(row)
            row.bind(pos=lambda w, _: _pill_bg(w), size=lambda w, _: _pill_bg(w))
            l = Label(text=lbl, font_size=sp(14), color=TEXT_MAIN,
                      halign="left", valign="middle")
            l.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
            v = Label(text=val, font_size=sp(14), color=TEXT_MUTED,
                      halign="right", valign="middle")
            v.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
            row.add_widget(l)
            row.add_widget(v)
            self._rows.add_widget(row)

    def _back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "monitor"


# ── App ────────────────────────────────────────────────────────────────────────

class PaceRingApp(App):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.profile = {
            "name": "friend", "resting_bpm": 65, "threshold": 110,
            "spike_delta": 30, "spike_duration": 10,
            "vibration": True, "sound_alerts": True,
        }

    def build(self):
        Window.clearcolor = BG
        saved = load_profile()
        if saved:
            self.profile.update(saved)

        sm = ScreenManager(transition=FadeTransition(duration=0.15))
        sm.add_widget(OnboardScreen1(name="onboard1"))
        sm.add_widget(OnboardScreen2(name="onboard2"))
        sm.add_widget(OnboardScreen3(name="onboard3"))
        sm.add_widget(MonitorScreen(name="monitor"))
        sm.add_widget(SummaryScreen(name="summary"))
        sm.add_widget(SettingsScreen(name="settings"))

        if saved and saved.get("name"):
            sm.current = "monitor"
            Clock.schedule_once(
                lambda dt: sm.get_screen("monitor").start_monitoring(), 0.5
            )
        else:
            sm.current = "onboard1"

        return sm

    def on_start(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.BLUETOOTH_SCAN,
                Permission.BLUETOOTH_CONNECT,
                Permission.ACCESS_FINE_LOCATION,
            ], lambda p, r: None)
        except ImportError:
            pass


if __name__ == "__main__":
    PaceRingApp().run()
