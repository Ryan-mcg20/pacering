"""
PaceRing — LUMINA Design System
Matches: Monitor, Summary, Onboarding, Profile, DevTools screens exactly.
"""

import json, os, time, math, random
from datetime import datetime, timedelta
from collections import deque

# ── Simulator toggle (also toggled in DevTools screen) ─────────────────────────
USE_SIMULATOR = True

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
    Color, Rectangle, RoundedRectangle, Line, Ellipse, Mesh,
    StencilPush, StencilUse, StencilPop, StencilUnUse,
)
from kivy.metrics import dp, sp
from kivy.properties import (
    NumericProperty, StringProperty, ListProperty, BooleanProperty,
)
from kivy.utils import get_color_from_hex

# ── LUMINA Palette (from DESIGN.md) ────────────────────────────────────────────
BG           = get_color_from_hex("#0d0f0c")   # surface-container-lowest
SURFACE      = get_color_from_hex("#121411")   # surface
CARD         = get_color_from_hex("#1e201d")   # surface-container
CARD_HIGH    = get_color_from_hex("#292b27")   # surface-container-high
CARD_HIGHEST = get_color_from_hex("#333531")   # surface-container-highest
PRIMARY      = get_color_from_hex("#d7baff")   # lavender
PRIMARY_C    = get_color_from_hex("#bd93f9")   # primary-container (vibrant violet)
ON_PRIMARY   = get_color_from_hex("#411478")
ON_SURFACE   = get_color_from_hex("#e3e3dd")
ON_VARIANT   = get_color_from_hex("#ccc3d3")
OUTLINE      = get_color_from_hex("#968e9c")
OUTLINE_VAR  = get_color_from_hex("#4a4451")
TERTIARY     = get_color_from_hex("#b5c5fc")
ERROR        = get_color_from_hex("#ffb4ab")
ERROR_C      = get_color_from_hex("#93000a")
GREEN        = get_color_from_hex("#4ade80")
AMBER        = get_color_from_hex("#fb923c")

PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".pacering_profile.json")
LOG_PATH     = os.path.join(os.path.expanduser("~"), ".pacering_log.json")
DEV_CODE     = "Ryan_5610"
SCENARIOS    = ["resting", "walking", "pots_spike", "sustained", "recovery"]
APP_VERSION  = "2.4.0"
APP_BUILD    = "892"


# ── Data helpers ───────────────────────────────────────────────────────────────

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
    log = log[-10000:]
    try:
        with open(LOG_PATH, "w") as f:
            json.dump(log, f)
    except Exception:
        pass

def greeting(name):
    h = datetime.now().hour
    if 5 <= h < 12:    return f"Good morning, {name}"
    elif 12 <= h < 17: return f"Good afternoon, {name}"
    elif 17 <= h < 22: return f"Good evening, {name}"
    else:              return f"Hey {name}, rest up"

def bpm_colour(bpm, resting, threshold):
    if bpm >= threshold:       return list(ERROR)
    elif bpm >= resting + 20:  return list(PRIMARY)
    else:                      return list(ON_SURFACE)


# ── Drawing helpers ────────────────────────────────────────────────────────────

def draw_card(widget, color=None, radius=16, border=True):
    """Attach glass-card background to a widget."""
    c = color or CARD
    with widget.canvas.before:
        Color(*c)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
        if border:
            Color(1, 1, 1, 0.08)
            brect = Line(
                rounded_rectangle=[widget.x, widget.y, widget.width, widget.height, dp(radius)],
                width=dp(0.8),
            )
    def _upd(*_):
        rect.pos = widget.pos
        rect.size = widget.size
        if border:
            brect.rounded_rectangle = [widget.x, widget.y, widget.width, widget.height, dp(radius)]
    widget.bind(pos=_upd, size=_upd)


def draw_bg(widget, color=None):
    c = color or BG
    with widget.canvas.before:
        Color(*c)
        bg = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(
        pos=lambda *_: setattr(bg, "pos", widget.pos),
        size=lambda *_: setattr(bg, "size", widget.size),
    )


# ── Top App Bar ────────────────────────────────────────────────────────────────

class TopBar(BoxLayout):
    def __init__(self, show_profile=True, show_notif=True, **kw):
        super().__init__(size_hint_y=None, height=dp(56),
                         padding=[dp(20), dp(8)], **kw)
        draw_bg(self, (0.04, 0.05, 0.04, 0.92))

        # Logo
        logo_row = BoxLayout(spacing=dp(6))
        logo_dot = Widget(size_hint=(None, None), size=(dp(22), dp(22)))
        with logo_dot.canvas:
            Color(*PRIMARY_C)
            Ellipse(pos=logo_dot.pos, size=logo_dot.size)
        logo_dot.bind(
            pos=lambda w, _: w.canvas.clear() or self._draw_dot(w),
            size=lambda w, _: w.canvas.clear() or self._draw_dot(w),
        )
        self._logo_dot = logo_dot

        logo_lbl = Label(
            text="PaceRing", font_size=sp(18), bold=True,
            color=PRIMARY_C, size_hint_x=None,
        )
        logo_lbl.texture_update()
        logo_lbl.size_hint_x = None
        logo_lbl.width = logo_lbl.texture_size[0] + dp(4)
        logo_row.add_widget(logo_dot)
        logo_row.add_widget(logo_lbl)
        self.add_widget(logo_row)
        self.add_widget(Widget())

        if show_notif:
            notif_btn = Button(
                text="", size_hint=(None, None), size=(dp(38), dp(38)),
                background_normal="", background_color=[0,0,0,0],
            )
            with notif_btn.canvas:
                Color(*ON_VARIANT)
                # Bell icon approximation
                Line(rounded_rectangle=[notif_btn.x+8, notif_btn.y+6,
                                        22, 20, 4], width=1.2)
            self.add_widget(notif_btn)

        if show_profile:
            avatar = Widget(size_hint=(None, None), size=(dp(32), dp(32)))
            with avatar.canvas:
                Color(*OUTLINE_VAR)
                Line(circle=(dp(16), dp(16), dp(15)), width=1)
                Color(*CARD_HIGH)
                Ellipse(pos=(dp(1), dp(1)), size=(dp(30), dp(30)))
            self.add_widget(avatar)

    def _draw_dot(self, w):
        with w.canvas:
            Color(*PRIMARY_C)
            Ellipse(pos=w.pos, size=w.size)


# ── Bottom Nav Bar ─────────────────────────────────────────────────────────────

class BottomNav(BoxLayout):
    def __init__(self, active="monitor", on_navigate=None, **kw):
        super().__init__(
            size_hint_y=None, height=dp(64),
            padding=[dp(8), dp(4)], **kw,
        )
        self._on_navigate = on_navigate
        draw_bg(self, (0.04, 0.05, 0.04, 0.92))

        with self.canvas.before:
            Color(1, 1, 1, 0.07)
            Line(points=[self.x, self.top, self.right, self.top], width=0.8)

        tabs = [
            ("monitor",  "Monitor"),
            ("summary",  "Summary"),
            ("devtools", "Tools"),
            ("profile",  "Profile"),
        ]
        for key, label in tabs:
            is_active = key == active
            btn = Button(
                text=label,
                font_size=sp(10), bold=True,
                color=PRIMARY_C if is_active else ON_VARIANT,
                background_normal="", background_color=[0,0,0,0],
            )
            if is_active:
                with btn.canvas.before:
                    Color(*PRIMARY_C[:3], 0.12)
                    rr = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])
                btn.bind(
                    pos=lambda b, _: setattr(rr, "pos", b.pos),
                    size=lambda b, _: setattr(rr, "size", b.size),
                )
            btn._nav_key = key
            btn.bind(on_release=self._nav)
            self.add_widget(btn)

    def _nav(self, btn):
        if self._on_navigate:
            self._on_navigate(btn._nav_key)


# ── ECG Line Graph ─────────────────────────────────────────────────────────────

class ECGLineGraph(Widget):
    """Scrolling ECG-style cardiac rhythm graph."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self._pts = deque(maxlen=80)
        self._phase = 0.0
        # Generate initial fake ECG waveform
        self._init_ecg()
        self.bind(pos=self._draw, size=self._draw)

    def _init_ecg(self):
        for i in range(80):
            t = i / 10.0
            v = self._ecg_val(t)
            self._pts.append(v)

    def _ecg_val(self, t):
        # Realistic ECG: flat, then P, QRS complex, T wave
        cycle = t % 1.0
        if cycle < 0.1:
            return 50 + random.gauss(0, 1)
        elif cycle < 0.15:
            return 50 + 8 * math.sin(math.pi * (cycle - 0.1) / 0.05) + random.gauss(0, 0.5)
        elif cycle < 0.25:
            return 50 + random.gauss(0, 1)
        elif cycle < 0.27:
            return 50 - 10 * (cycle - 0.25) / 0.02 + random.gauss(0, 0.5)
        elif cycle < 0.30:
            return 50 - 10 + 70 * (cycle - 0.27) / 0.03 + random.gauss(0, 0.5)
        elif cycle < 0.33:
            return 50 + 60 - 80 * (cycle - 0.30) / 0.03 + random.gauss(0, 0.5)
        elif cycle < 0.38:
            return 50 - 20 + 20 * (cycle - 0.33) / 0.05 + random.gauss(0, 0.5)
        elif cycle < 0.55:
            return 50 + 15 * math.sin(math.pi * (cycle - 0.38) / 0.17) + random.gauss(0, 0.5)
        else:
            return 50 + random.gauss(0, 0.8)

    def tick(self):
        self._phase += 0.1
        self._pts.append(self._ecg_val(self._phase))
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*CARD)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])

        if len(self._pts) < 2 or self.width < 2:
            return

        pts = list(self._pts)
        mn, mx = min(pts), max(pts)
        rng = max(mx - mn, 30)
        w, h = self.size
        px, py = self.pos
        pad = dp(10)
        uw = (w - 2*pad) / max(1, len(pts) - 1)

        points = []
        for i, v in enumerate(pts):
            x = px + pad + i * uw
            y = py + pad + ((v - mn) / rng) * (h - 2*pad)
            points += [x, y]

        with self.canvas:
            # Gradient fill
            fv = [points[0], py + pad, 0, 0]
            for i in range(0, len(points), 2):
                fv += [points[i], points[i+1], 0, 0]
            fv += [points[-2], py + pad, 0, 0]
            Color(*PRIMARY_C[:3], 0.12)
            Mesh(vertices=fv, indices=list(range(len(fv)//4)), mode='triangle_fan')
            # Line
            Color(*PRIMARY_C[:3], 0.5)
            Line(points=points, width=dp(1.4), cap="round", joint="round")


# ── BPM Bar Chart ──────────────────────────────────────────────────────────────

class BPMBarChart(Widget):
    data = ListProperty([])  # list of (label, value, is_highlight)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, data=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        if not self.data:
            return
        n = len(self.data)
        w, h = self.size
        px, py = self.pos
        pad = dp(8)
        gap = dp(6)
        bar_w = (w - 2*pad - gap*(n-1)) / n
        max_v = max(v for _, v, _ in self.data) or 1

        with self.canvas:
            for i, (label, val, highlight) in enumerate(self.data):
                bx = px + pad + i * (bar_w + gap)
                bar_h = max(dp(4), (val / max_v) * (h - dp(28)))
                by = py + dp(18)

                # Background bar
                Color(1, 1, 1, 0.05)
                RoundedRectangle(pos=(bx, by), size=(bar_w, h - dp(18)),
                                 radius=[dp(4), dp(4), dp(4), dp(4)])

                # Value bar
                if highlight:
                    Color(*PRIMARY_C)
                else:
                    Color(*CARD_HIGHEST)
                RoundedRectangle(pos=(bx, by), size=(bar_w, bar_h),
                                 radius=[dp(4), dp(4), dp(4), dp(4)])


# ── Heart Pulse Widget ─────────────────────────────────────────────────────────

class HeartPulse(Widget):
    """Large pulsing heart circle matching the Monitor screen design."""
    pulse_scale = NumericProperty(1.0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._bpm = 74
        self._pulse_ev = None
        self.bind(pos=self._draw, size=self._draw, pulse_scale=self._draw)

    def set_bpm(self, bpm):
        self._bpm = max(40, min(200, bpm))
        if self._pulse_ev:
            self._pulse_ev.cancel()
        interval = 60.0 / self._bpm
        self._pulse_ev = Clock.schedule_interval(self._beat, interval)

    def _beat(self, dt):
        anim = (
            Animation(pulse_scale=1.12, duration=0.10, t="out_quad") +
            Animation(pulse_scale=0.97, duration=0.07, t="in_quad") +
            Animation(pulse_scale=1.0,  duration=0.13, t="out_quad")
        )
        anim.start(self)

    def _draw(self, *_):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        s = self.pulse_scale
        r = min(self.width, self.height) * 0.44 * s

        with self.canvas:
            # Outer ambient glow (bio-pulse)
            Color(*PRIMARY_C[:3], 0.06)
            Ellipse(pos=(cx - r*1.7, cy - r*1.7), size=(r*3.4, r*3.4))
            Color(*PRIMARY_C[:3], 0.09)
            Ellipse(pos=(cx - r*1.35, cy - r*1.35), size=(r*2.7, r*2.7))

            # Main circle fill
            Color(*PRIMARY_C[:3], 0.07)
            Ellipse(pos=(cx - r, cy - r), size=(r*2, r*2))

            # Circle border
            Color(*PRIMARY_C[:3], 0.22)
            Line(circle=(cx, cy, r), width=dp(1.5))

            # Inner glow ring
            Color(*PRIMARY_C[:3], 0.15)
            Line(circle=(cx, cy, r * 0.85), width=dp(0.8))

            # Heart icon (simplified using bezier-like path)
            hr = r * 0.35
            # Heart using parametric
            pts = []
            for i in range(60):
                t = (i / 60) * 2 * math.pi
                hx = 16 * (math.sin(t)**3)
                hy = 13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t)
                nx = cx + (hx / 17.0) * hr
                ny = cy + dp(8) + (hy / 17.0) * hr
                pts.extend([nx, ny])

            Color(*PRIMARY_C)
            Line(points=pts, width=dp(2.2), close=True)

    def stop(self):
        if self._pulse_ev:
            self._pulse_ev.cancel()
            self._pulse_ev = None


# ── Toggle Switch Widget ───────────────────────────────────────────────────────

class ToggleSwitch(Widget):
    active = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(size_hint=(None, None), size=(dp(44), dp(24)), **kw)
        self.bind(pos=self._draw, size=self._draw, active=self._draw)
        self.bind(on_touch_down=self._touched)

    def _touched(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.active = not self.active
            return True

    def _draw(self, *_):
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        with self.canvas:
            if self.active:
                Color(*PRIMARY_C)
            else:
                Color(*CARD_HIGHEST)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[dp(12)])
            Color(1, 1, 1, 1)
            knob_x = x + w - dp(20) if self.active else x + dp(4)
            Ellipse(pos=(knob_x, y + dp(4)), size=(dp(16), dp(16)))


# ── Reusable Widgets ───────────────────────────────────────────────────────────

class PurpleButton(Button):
    def __init__(self, text="", danger=False, ghost=False, **kw):
        super().__init__(
            text=text,
            font_size=sp(15), bold=True,
            background_normal="", background_color=[0,0,0,0],
            color=ON_PRIMARY if not ghost else PRIMARY,
            size_hint_y=None, height=dp(52),
            **kw,
        )
        self._danger = danger
        self._ghost = ghost
        bg = ERROR_C if danger else (SURFACE if ghost else PRIMARY_C)
        with self.canvas.before:
            self._col = Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(26)])
            if ghost:
                Color(*PRIMARY_C, 0.3)
                self._border = Line(
                    rounded_rectangle=[self.x, self.y, self.width, self.height, dp(26)],
                    width=dp(0.8),
                )
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        if self._ghost:
            self._border.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(26)]

    def on_press(self):
        self._col.rgba = list(ON_PRIMARY[:3]) + [0.3] if not self._danger else list(ERROR[:3]) + [0.5]
    def on_release(self):
        bg = ERROR_C if self._danger else (SURFACE if self._ghost else PRIMARY_C)
        self._col.rgba = list(bg)


class ScenarioChip(Button):
    def __init__(self, text="", icon="", active=False, **kw):
        super().__init__(
            text=f"  {text}",
            font_size=sp(13), bold=True,
            background_normal="", background_color=[0,0,0,0],
            color=PRIMARY_C if active else ON_VARIANT,
            size_hint_y=None, height=dp(44),
            **kw,
        )
        self._active = active
        with self.canvas.before:
            Color(*(PRIMARY_C[:3] + [0.18]) if active else list(CARD_HIGH) + [1.0])
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*(PRIMARY_C[:3] + [0.4]) if active else list(OUTLINE_VAR) + [1.0])
            self._brd = Line(
                rounded_rectangle=[self.x, self.y, self.width, self.height, dp(8)],
                width=dp(0.7),
            )
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._brd.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(8)]


class StatChip(BoxLayout):
    """Small metric tile: icon + label + big number + progress bar."""
    def __init__(self, icon="", label="", value="--", unit="", bar=0.65, **kw):
        super().__init__(
            orientation="vertical",
            padding=[dp(14), dp(12)],
            spacing=dp(6),
            **kw,
        )
        draw_card(self, CARD, radius=12)

        top = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(6))
        top.add_widget(Label(text=icon, font_size=sp(15), color=ON_VARIANT,
                             size_hint_x=None, width=dp(22)))
        top.add_widget(Label(text=label, font_size=sp(10), color=ON_VARIANT,
                             halign="left"))
        self.add_widget(top)

        val_row = BoxLayout(size_hint_y=None, height=dp(32))
        self._val_lbl = Label(text=str(value), font_size=sp(24), bold=True,
                              color=ON_SURFACE, halign="left")
        val_row.add_widget(self._val_lbl)
        if unit:
            val_row.add_widget(Label(text=unit, font_size=sp(13),
                                     color=ON_VARIANT, size_hint_x=None, width=dp(28)))
        self.add_widget(val_row)

        # Progress bar
        bar_bg = Widget(size_hint_y=None, height=dp(4))
        with bar_bg.canvas:
            Color(1, 1, 1, 0.05)
            self._bar_bg_r = RoundedRectangle(pos=bar_bg.pos, size=bar_bg.size,
                                               radius=[dp(2)])
            Color(*PRIMARY_C)
            self._bar_fill = RoundedRectangle(
                pos=bar_bg.pos,
                size=(bar_bg.width * bar, bar_bg.height),
                radius=[dp(2)],
            )
        bar_bg.bind(pos=self._upd_bar, size=self._upd_bar)
        self._bar_widget = bar_bg
        self._bar_pct = bar
        self.add_widget(bar_bg)

    def _upd_bar(self, w, _):
        self._bar_bg_r.pos = w.pos
        self._bar_bg_r.size = w.size
        self._bar_fill.pos = w.pos
        self._bar_fill.size = (w.width * self._bar_pct, w.height)

    def set_value(self, v, color=None):
        self._val_lbl.text = str(v)
        if color:
            self._val_lbl.color = color

    def set_bar(self, pct):
        self._bar_pct = max(0, min(1, pct))
        self._upd_bar(self._bar_widget, None)


class SettingRow(BoxLayout):
    """Profile setting row: icon + label + right content."""
    def __init__(self, icon="", label="", right_text="", right_widget=None,
                 on_press_cb=None, **kw):
        super().__init__(
            size_hint_y=None, height=dp(56),
            padding=[dp(0), dp(0)],
            spacing=dp(12),
            **kw,
        )
        draw_card(self, CARD, radius=10)

        inner = BoxLayout(padding=[dp(16), 0], spacing=dp(12))

        # Icon
        inner.add_widget(Label(
            text=icon, font_size=sp(18), color=ON_VARIANT,
            size_hint=(None, 1), width=dp(28),
        ))

        # Label
        lbl = Label(text=label, font_size=sp(15), color=ON_SURFACE,
                    halign="left", valign="middle")
        lbl.bind(size=lambda w, _: setattr(w, "text_size", w.size))
        inner.add_widget(lbl)

        if right_widget:
            inner.add_widget(right_widget)
        elif right_text:
            rl = Label(text=right_text, font_size=sp(14), color=ON_VARIANT,
                       halign="right", size_hint_x=None)
            rl.texture_update()
            rl.width = rl.texture_size[0] + dp(8)
            inner.add_widget(rl)

        self.add_widget(inner)

        if on_press_cb:
            btn_overlay = Button(
                background_normal="", background_color=[0,0,0,0],
                size_hint=(1, 1), pos_hint={"x": 0, "y": 0},
            )
            btn_overlay.bind(on_release=on_press_cb)
            self.add_widget(btn_overlay)


# ── Screen helpers ─────────────────────────────────────────────────────────────

def _nav(manager, key):
    manager.transition = FadeTransition(duration=0.12)
    manager.current = key


# ── Onboarding Screen 1 ────────────────────────────────────────────────────────

class OnboardScreen1(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        draw_bg(root)

        # Ambient glow bg
        with root.canvas.before:
            Color(*PRIMARY_C[:3], 0.04)
            Ellipse(pos=(root.width*0.4, root.height*0.5), size=(dp(300), dp(300)))

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(72), dp(24), dp(32)],
            spacing=dp(0), size_hint=(1, 1),
        )

        # Step label
        step_lbl = Label(
            text="ONBOARDING PHASE", font_size=sp(11),
            color=(*PRIMARY[:3], 0.7), size_hint_y=None, height=dp(24),
            halign="left",
        )
        step_lbl.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(step_lbl)
        col.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # Big title
        title = Label(
            text="PaceRing", font_size=sp(44), bold=True,
            color=ON_SURFACE, size_hint_y=None, height=dp(60), halign="left",
        )
        title.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(title)

        subtitle = Label(
            text="Let's fine-tune your profile for\nclinical precision and restorative calm.",
            font_size=sp(15), color=ON_VARIANT,
            size_hint_y=None, height=dp(52), halign="left",
        )
        subtitle.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(subtitle)

        col.add_widget(Widget(size_hint_y=None, height=dp(24)))

        # Sync animation card
        sync_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(160),
            padding=[dp(16), dp(16)],
        )
        draw_card(sync_card, CARD, radius=16)

        sync_inner = BoxLayout(orientation="vertical", spacing=dp(8))
        # Pulse circle
        pulse_box = BoxLayout(size_hint_y=None, height=dp(72))
        pulse_circle = Widget()
        with pulse_circle.canvas:
            Color(*PRIMARY_C[:3], 0.2)
            Ellipse(pos=(pulse_circle.center_x - dp(30), pulse_circle.center_y - dp(30)),
                    size=(dp(60), dp(60)))
            Color(*PRIMARY_C)
            Line(circle=(pulse_circle.center_x, pulse_circle.center_y, dp(24)), width=dp(1.5))
            Ellipse(pos=(pulse_circle.center_x - dp(18), pulse_circle.center_y - dp(18)),
                    size=(dp(36), dp(36)))

        def _redraw_pulse(w, _):
            w.canvas.clear()
            cx, cy = w.center_x, w.center_y
            with w.canvas:
                Color(*PRIMARY_C[:3], 0.2)
                Ellipse(pos=(cx - dp(30), cy - dp(30)), size=(dp(60), dp(60)))
                Color(*PRIMARY_C)
                Line(circle=(cx, cy, dp(24)), width=dp(1.5))
                Color(*ON_PRIMARY)
                Ellipse(pos=(cx - dp(18), cy - dp(18)), size=(dp(36), dp(36)))

        pulse_circle.bind(pos=_redraw_pulse, size=_redraw_pulse)
        pulse_box.add_widget(pulse_circle)
        sync_inner.add_widget(pulse_box)

        sync_inner.add_widget(Label(
            text="Awaiting Sync", font_size=sp(16), bold=True,
            color=ON_SURFACE, size_hint_y=None, height=dp(24),
        ))
        sync_inner.add_widget(Label(
            text="Optimizing clinical sensor feedback...",
            font_size=sp(13), color=ON_VARIANT, size_hint_y=None, height=dp(20),
        ))

        # Progress bar
        prog = Widget(size_hint_y=None, height=dp(4))
        with prog.canvas:
            Color(1, 1, 1, 0.05)
            RoundedRectangle(pos=prog.pos, size=prog.size, radius=[dp(2)])
            Color(*PRIMARY_C)
            self._prog_fill = RoundedRectangle(
                pos=prog.pos, size=(0, prog.height), radius=[dp(2)]
            )
        prog.bind(pos=lambda w, _: setattr(self._prog_fill, "pos", w.pos),
                  size=lambda w, _: setattr(self._prog_fill, "size", (w.width * 0.33, w.height)))
        sync_inner.add_widget(prog)

        sync_card.add_widget(sync_inner)
        col.add_widget(sync_card)

        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        # Personal Baseline card
        baseline_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(160),
            padding=[dp(16), dp(14)], spacing=dp(12),
        )
        draw_card(baseline_card, CARD, radius=16)

        # Title with accent bar
        bl_title_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(10))
        accent_bar = Widget(size_hint=(None, None), size=(dp(3), dp(28)))
        with accent_bar.canvas:
            Color(*PRIMARY_C)
            RoundedRectangle(pos=accent_bar.pos, size=accent_bar.size, radius=[dp(2)])
        accent_bar.bind(
            pos=lambda w, _: w.canvas.clear() or _draw_accent(w),
            size=lambda w, _: w.canvas.clear() or _draw_accent(w),
        )
        def _draw_accent(w):
            with w.canvas:
                Color(*PRIMARY_C)
                RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(2)])

        bl_title_row.add_widget(accent_bar)
        bl_title_row.add_widget(Label(
            text="Personal Baseline", font_size=sp(22), bold=True,
            color=ON_SURFACE, halign="left",
        ))
        baseline_card.add_widget(bl_title_row)

        # Name input
        name_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(0))
        with name_box.canvas.before:
            Color(*CARD_HIGH)
            nr = RoundedRectangle(pos=name_box.pos, size=name_box.size,
                                  radius=[dp(6), dp(6), 0, 0])
            Color(*OUTLINE_VAR)
            nb = Line(points=[name_box.x, name_box.y, name_box.right, name_box.y], width=1.5)
        name_box.bind(
            pos=lambda w, _: setattr(nr, "pos", w.pos) or setattr(nb, "points",
                [w.x, w.y, w.right, w.y]),
            size=lambda w, _: setattr(nr, "size", w.size) or setattr(nb, "points",
                [w.x, w.y, w.right, w.y]),
        )
        self.name_input = TextInput(
            hint_text="Enter your name",
            hint_text_color=(*OUTLINE[:3], 0.7),
            foreground_color=ON_SURFACE,
            background_color=[0,0,0,0],
            cursor_color=PRIMARY_C,
            font_size=sp(15),
            padding=[dp(12), dp(10)],
            multiline=False,
        )
        name_box.add_widget(self.name_input)
        baseline_card.add_widget(name_box)

        # HR input
        hr_box = BoxLayout(size_hint_y=None, height=dp(44))
        with hr_box.canvas.before:
            Color(*CARD_HIGH)
            hr_r = RoundedRectangle(pos=hr_box.pos, size=hr_box.size,
                                    radius=[dp(6), dp(6), 0, 0])
            Color(*OUTLINE_VAR)
            hr_b = Line(points=[hr_box.x, hr_box.y, hr_box.right, hr_box.y], width=1.5)
        hr_box.bind(
            pos=lambda w, _: setattr(hr_r, "pos", w.pos) or setattr(hr_b, "points",
                [w.x, w.y, w.right, w.y]),
            size=lambda w, _: setattr(hr_r, "size", w.size) or setattr(hr_b, "points",
                [w.x, w.y, w.right, w.y]),
        )
        self.hr_input = TextInput(
            hint_text="60",
            hint_text_color=(*OUTLINE[:3], 0.7),
            foreground_color=ON_SURFACE,
            background_color=[0,0,0,0],
            cursor_color=PRIMARY_C,
            font_size=sp(15),
            padding=[dp(12), dp(10)],
            multiline=False, input_filter="int",
        )
        hr_box.add_widget(self.hr_input)
        baseline_card.add_widget(hr_box)

        col.add_widget(baseline_card)

        col.add_widget(Widget(size_hint_y=None, height=dp(16)))

        # Sensitivity card
        sens_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(160),
            padding=[dp(16), dp(14)], spacing=dp(10),
        )
        draw_card(sens_card, CARD, radius=16)

        sens_title_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(10))
        accent2 = Widget(size_hint=(None, None), size=(dp(3), dp(28)))
        def _draw_a2(w, _=None):
            w.canvas.clear()
            with w.canvas:
                Color(*PRIMARY_C)
                RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(2)])
        accent2.bind(pos=_draw_a2, size=_draw_a2)
        sens_title_row.add_widget(accent2)
        sens_title_row.add_widget(Label(
            text="Sensitivity Threshold", font_size=sp(20), bold=True,
            color=ON_SURFACE, halign="left",
        ))
        sens_card.add_widget(sens_title_row)

        # Radio options
        self._sens = "medium"
        opts_row = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(80))
        for opt in ["Low", "Medium", "High"]:
            ob = BoxLayout(orientation="vertical", padding=[dp(8), dp(8)])
            active = opt.lower() == "medium"
            with ob.canvas.before:
                Color(*(PRIMARY_C[:3] + [0.14]) if active else list(CARD_HIGH) + [1])
                ob_bg = RoundedRectangle(pos=ob.pos, size=ob.size, radius=[dp(8)])
                Color(*(PRIMARY_C[:3] + [0.4]) if active else list(OUTLINE_VAR) + [1])
                ob_brd = Line(
                    rounded_rectangle=[ob.x, ob.y, ob.width, ob.height, dp(8)],
                    width=0.8,
                )
            ob.bind(
                pos=lambda w, _, bg=ob_bg, brd=ob_brd: (
                    setattr(bg, "pos", w.pos),
                    setattr(brd, "rounded_rectangle", [w.x, w.y, w.width, w.height, dp(8)]),
                ),
                size=lambda w, _, bg=ob_bg, brd=ob_brd: (
                    setattr(bg, "size", w.size),
                    setattr(brd, "rounded_rectangle", [w.x, w.y, w.width, w.height, dp(8)]),
                ),
            )
            ob.add_widget(Label(
                text=opt, font_size=sp(12), bold=True,
                color=PRIMARY_C if active else ON_VARIANT,
                size_hint_y=None, height=dp(22),
            ))
            ob.add_widget(Label(
                text="Standard\nbalance." if opt == "Medium" else
                     "Clinical\ndampening." if opt == "Low" else
                     "Precision\nfocus.",
                font_size=sp(10), color=OUTLINE,
            ))
            opts_row.add_widget(ob)
        sens_card.add_widget(opts_row)
        col.add_widget(sens_card)

        col.add_widget(Widget())

        # Step dots + CTA
        dots_row = BoxLayout(size_hint_y=None, height=dp(20))
        dots_row.add_widget(Widget(size_hint_x=None, width=dp(24)))
        for i, (w_val, color_val) in enumerate([(dp(20), PRIMARY_C), (dp(8), CARD_HIGHEST), (dp(8), CARD_HIGHEST)]):
            dot = Widget(size_hint=(None, None), size=(w_val, dp(4)))
            with dot.canvas:
                Color(*color_val)
                RoundedRectangle(pos=dot.pos, size=dot.size, radius=[dp(2)])
            dot.bind(
                pos=lambda w, _, c=color_val, ww=w_val: w.canvas.clear() or
                    setattr(w, "canvas", w.canvas) or _draw_dot_bar(w, c),
                size=lambda w, _, c=color_val: _draw_dot_bar(w, c),
            )
            dots_row.add_widget(dot)
        dots_row.add_widget(Widget())
        status_lbl = Label(
            text="CONFIGURATION STATUS: READY",
            font_size=sp(10), color=OUTLINE,
            size_hint_x=None,
        )
        status_lbl.texture_update()
        status_lbl.width = status_lbl.texture_size[0]
        dots_row.add_widget(status_lbl)
        dots_row.add_widget(Widget(size_hint_x=None, width=dp(8)))
        col.add_widget(dots_row)
        col.add_widget(Widget(size_hint_y=None, height=dp(8)))

        begin_btn = PurpleButton(text="Begin Experience  ->")
        begin_btn.bind(on_release=self._next)
        col.add_widget(begin_btn)

        root.add_widget(col)
        self.add_widget(root)

    def _next(self, *_):
        p = App.get_running_app().profile
        name = self.name_input.text.strip() or "Ryan"
        resting = int(self.hr_input.text or 65)
        p["name"] = name
        p["resting_bpm"] = resting
        p["threshold"] = resting + 45
        p["spike_delta"] = 30
        p["spike_duration"] = 10
        p["vibration"] = True
        p["sound_alerts"] = True
        save_profile(p)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "monitor"
        App.get_running_app().root.get_screen("monitor").start_monitoring()


def _draw_dot_bar(w, color):
    w.canvas.clear()
    with w.canvas:
        Color(*color)
        RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(2)])


# ── Monitor Screen ─────────────────────────────────────────────────────────────

class MonitorScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._worker = None
        self._alert_engine = None
        self._dev_taps = []
        self._alert_up = False
        self._ecg_event = None
        self._build()

    def _build(self):
        root = FloatLayout()
        draw_bg(root)

        col = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
        )

        # Top bar
        self._topbar = TopBar()
        col.add_widget(self._topbar)

        # Scrollable content
        sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(12), dp(20), dp(16)],
            spacing=dp(20), size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        # Greeting
        self.greeting_lbl = Label(
            text="LIVE FEED", font_size=sp(11),
            color=(*PRIMARY[:3], 0.6),
            size_hint_y=None, height=dp(18), halign="left",
        )
        self.greeting_lbl.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        content.add_widget(self.greeting_lbl)

        self.greeting_name = Label(
            text="Good morning, Ryan",
            font_size=sp(28), bold=True, color=ON_SURFACE,
            size_hint_y=None, height=dp(42), halign="left",
        )
        self.greeting_name.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        content.add_widget(self.greeting_name)

        # Heart pulse centerpiece
        pulse_area = FloatLayout(size_hint_y=None, height=dp(280))

        # Bio-pulse background glow
        with pulse_area.canvas.before:
            Color(*PRIMARY_C[:3], 0.06)
            Ellipse(pos=(dp(60), dp(40)), size=(dp(240), dp(240)))

        self.heart = HeartPulse(
            size_hint=(None, None), size=(dp(220), dp(220)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        pulse_area.add_widget(self.heart)

        # BPM number inside heart
        bpm_box = BoxLayout(
            orientation="vertical",
            size_hint=(None, None), size=(dp(160), dp(70)),
            pos_hint={"center_x": 0.5, "center_y": 0.46},
        )
        self.bpm_lbl = Label(
            text="74", font_size=sp(60), bold=True,
            color=PRIMARY, size_hint_y=None, height=dp(54),
        )
        bpm_unit = Label(text="BPM", font_size=sp(11), color=(*PRIMARY[:3], 0.6),
                         size_hint_y=None, height=dp(16))
        bpm_box.add_widget(self.bpm_lbl)
        bpm_box.add_widget(bpm_unit)
        pulse_area.add_widget(bpm_box)

        content.add_widget(pulse_area)

        # Status pill
        self.status_pill = BoxLayout(
            size_hint=(None, None), size=(dp(160), dp(32)),
            pos_hint_x=0,
        )
        status_outer = BoxLayout(size_hint_y=None, height=dp(32))
        self._status_pill_widget = BoxLayout(
            size_hint=(None, None), size=(dp(160), dp(32)),
            padding=[dp(12), dp(6)], spacing=dp(8),
        )
        draw_card(self._status_pill_widget, CARD, radius=16)

        dot = Widget(size_hint=(None, None), size=(dp(8), dp(8)))
        with dot.canvas:
            Color(*PRIMARY_C)
            Ellipse(pos=dot.pos, size=dot.size)
        dot.bind(
            pos=lambda w, _: w.canvas.clear() or self._draw_dot(w),
            size=lambda w, _: w.canvas.clear() or self._draw_dot(w),
        )
        self._status_dot = dot

        self._status_pill_widget.add_widget(dot)
        self.status_lbl = Label(
            text="Pacing Optimal", font_size=sp(11), bold=True, color=PRIMARY,
        )
        self._status_pill_widget.add_widget(self.status_lbl)
        status_outer.add_widget(self._status_pill_widget)
        status_outer.add_widget(Widget())
        content.add_widget(status_outer)

        # ECG rhythm section
        ecg_hdr = BoxLayout(size_hint_y=None, height=dp(24))
        ecg_hdr.add_widget(Label(
            text="Cardiac Rhythm", font_size=sp(11), bold=True,
            color=ON_VARIANT, halign="left",
        ))
        ecg_hdr.add_widget(Label(
            text="REAL-TIME", font_size=sp(11), bold=True,
            color=PRIMARY, halign="right",
        ))
        content.add_widget(ecg_hdr)

        self.ecg = ECGLineGraph(size_hint_y=None, height=dp(90))
        content.add_widget(self.ecg)

        # Stat chips row
        chips = GridLayout(cols=2, spacing=dp(12), size_hint_y=None, height=dp(110))
        self.chip_hrv   = StatChip(icon="m", label="HRV VARIANCE",  value="62", unit="ms", bar=0.65)
        self.chip_rest  = StatChip(icon=")", label="REST SCORE",     value="88", unit="%",  bar=0.88)
        chips.add_widget(self.chip_hrv)
        chips.add_widget(self.chip_rest)
        content.add_widget(chips)

        # Connect button
        self.connect_btn = PurpleButton(text="connect to band")
        self.connect_btn.bind(on_release=self._connect_pressed)
        content.add_widget(self.connect_btn)

        sv.add_widget(content)
        col.add_widget(sv)

        # Bottom nav
        col.add_widget(BottomNav(active="monitor", on_navigate=lambda k: _nav(self.manager, k)))

        root.add_widget(col)

        # Alert card
        self._alert_card = self._make_alert_card()
        root.add_widget(self._alert_card)

        self.add_widget(root)
        self._root = root

    def _draw_dot(self, w):
        with w.canvas:
            Color(*PRIMARY_C)
            Ellipse(pos=w.pos, size=w.size)

    def _make_alert_card(self):
        card = FloatLayout(size_hint=(1, None), height=dp(170))
        card.y = -dp(200)
        draw_card(card, CARD_HIGH, radius=20)
        with card.canvas.before:
            Color(*PRIMARY_C[:3], 0.4)
            Line(rounded_rectangle=[card.x, card.y, card.width, card.height, dp(20)],
                 width=dp(1.2))

        inner = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(18), dp(24), dp(14)],
            spacing=dp(8), size_hint=(1, 1),
        )
        self.alert_title = Label(
            text="spike detected", font_size=sp(17), bold=True,
            color=ON_SURFACE, halign="left", size_hint_y=None, height=dp(28),
        )
        self.alert_title.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        self.alert_msg = Label(
            text="", font_size=sp(13), color=ON_VARIANT,
            halign="left", size_hint_y=None, height=dp(38),
        )
        self.alert_msg.bind(size=lambda w, _: setattr(w, "text_size", (w.width, dp(38))))
        dismiss = PurpleButton(text="ok - resting now", height=dp(44))
        dismiss.bind(on_release=self._dismiss_alert)
        inner.add_widget(self.alert_title)
        inner.add_widget(self.alert_msg)
        inner.add_widget(dismiss)
        card.add_widget(inner)
        return card

    def on_enter(self):
        self._refresh_profile()
        self._ecg_event = Clock.schedule_interval(lambda dt: self.ecg.tick(), 0.12)

    def on_leave(self):
        if self._ecg_event:
            self._ecg_event.cancel()
            self._ecg_event = None

    def _refresh_profile(self):
        p = App.get_running_app().profile
        name = p.get("name", "Ryan")
        self.greeting_name.text = greeting(name)

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
        import threading
        threading.Thread(target=self._ble_thread, daemon=True).start()

    def _ble_thread(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._ble_main())

    async def _ble_main(self):
        from bleak import BleakScanner, BleakClient
        Clock.schedule_once(lambda dt: setattr(self.status_lbl, "text", "scanning..."), 0)
        devices = await BleakScanner.discover(timeout=30.0)
        keywords = ["mi band", "xiaomi", "band 10", "smart band", "miband"]
        address = None
        for d in devices:
            if d.name and any(k in d.name.lower() for k in keywords):
                address = d.address
                break
        if not address:
            Clock.schedule_once(lambda dt: setattr(self.status_lbl, "text",
                                                   "band not found"), 0)
            return
        try:
            async with BleakClient(address, timeout=20.0) as client:
                Clock.schedule_once(lambda dt: setattr(self.status_lbl, "text",
                                                       "connected"), 0)
                HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
                await client.start_notify(HR_UUID, self._ble_handler)
                while client.is_connected:
                    await asyncio.sleep(0.5)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status_lbl, "text", f"err: {e}"), 0)

    def _ble_handler(self, sender, data):
        flags = data[0]
        bpm = int.from_bytes(data[1:3], "little") if (flags & 1) else data[1]
        Clock.schedule_once(lambda dt: self._on_bpm(bpm, None), 0)

    def _on_bpm(self, bpm, rmssd):
        p = App.get_running_app().profile
        resting = p.get("resting_bpm", 65)
        threshold = p.get("threshold", 110)

        self.bpm_lbl.text = str(bpm)
        Animation(color=bpm_colour(bpm, resting, threshold), duration=0.4).start(self.bpm_lbl)
        self.heart.set_bpm(bpm)

        if rmssd is not None:
            self.chip_hrv.set_value(str(int(rmssd)))
            self.chip_hrv.set_bar(min(1.0, rmssd / 100.0))

        append_log({
            "ts": datetime.now().isoformat(),
            "bpm": bpm,
            "rmssd": int(rmssd) if rmssd else None,
        })

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
        self.alert_msg.text = msg
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
                self._alert_engine._spike_alerted = False
                self._alert_engine._sustained_alerted = False
                self._alert_engine._sustained_start = None
        anim = Animation(y=-dp(200), duration=0.25, t="in_quad")
        anim.bind(on_complete=_done)
        anim.start(self._alert_card)

    def _connect_pressed(self, *_):
        self.connect_btn.text = "connecting..."
        self.connect_btn.disabled = True
        Clock.schedule_once(lambda dt: self.start_monitoring(), 0.1)

    def _initial_tapped(self, *_):
        now = time.time()
        self._dev_taps = [t for t in self._dev_taps if now - t < 1.5]
        self._dev_taps.append(now)
        if len(self._dev_taps) >= 5:
            self._dev_taps = []
            _nav(self.manager, "devtools")


# ── Summary Screen ─────────────────────────────────────────────────────────────

class SummaryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        draw_bg(root)
        col = BoxLayout(orientation="vertical", size_hint=(1, 1))
        col.add_widget(TopBar())
        sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self._content = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(12), dp(20), dp(16)],
            spacing=dp(16), size_hint_y=None,
        )
        self._content.bind(minimum_height=self._content.setter("height"))
        sv.add_widget(self._content)
        col.add_widget(sv)
        col.add_widget(BottomNav(active="summary", on_navigate=lambda k: _nav(self.manager, k)))
        root.add_widget(col)
        self.add_widget(root)

    def on_enter(self):
        self._content.clear_widgets()
        self._build_content()

    def _build_content(self):
        c = self._content
        p = App.get_running_app().profile
        name = p.get("name", "Ryan")
        stats = self._compute_stats()

        # Title
        c.add_widget(Label(
            text="Weekly Insights", font_size=sp(28), bold=True,
            color=PRIMARY, size_hint_y=None, height=dp(42), halign="left",
        ))
        summary_txt = Label(
            text=f"Your physiological markers show a consistent trend towards optimal recovery. "
                 f"Cardiovascular efficiency improved by 4% compared to the previous week, "
                 f"driven by stable HRV levels.",
            font_size=sp(14), color=ON_VARIANT,
            size_hint_y=None, halign="left",
        )
        summary_txt.bind(size=lambda w, _: (
            setattr(w, "text_size", (w.width, None)),
            w.texture_update(),
            setattr(w, "height", w.texture_size[1] + dp(8)),
        ))
        c.add_widget(summary_txt)

        # Avg BPM card with bar chart
        bpm_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(280),
            padding=[dp(16), dp(14)], spacing=dp(10),
        )
        draw_card(bpm_card, CARD, radius=14)

        bpm_top = BoxLayout(size_hint_y=None, height=dp(56))
        bpm_left = BoxLayout(orientation="vertical")
        bpm_left.add_widget(Label(
            text="AVERAGE DAILY BPM", font_size=sp(10), bold=True,
            color=ON_VARIANT, halign="left", size_hint_y=None, height=dp(16),
        ))
        bpm_num_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        bpm_num_row.add_widget(Label(
            text=str(stats["avg_bpm"]), font_size=sp(42), bold=True,
            color=ON_SURFACE, size_hint_x=None, width=dp(90),
        ))
        bpm_num_row.add_widget(Label(
            text="BPM", font_size=sp(16), color=PRIMARY,
            halign="left",
        ))
        bpm_left.add_widget(bpm_num_row)
        bpm_top.add_widget(bpm_left)

        # OPTIMAL chip
        opt_chip = BoxLayout(
            size_hint=(None, None), size=(dp(90), dp(28)),
            padding=[dp(10), dp(4)], spacing=dp(6),
        )
        with opt_chip.canvas.before:
            Color(*PRIMARY[:3], 0.12)
            opt_bg = RoundedRectangle(pos=opt_chip.pos, size=opt_chip.size, radius=[dp(14)])
            Color(*PRIMARY[:3], 0.25)
            opt_brd = Line(
                rounded_rectangle=[opt_chip.x, opt_chip.y, opt_chip.width, opt_chip.height, dp(14)],
                width=0.8,
            )
        opt_chip.bind(
            pos=lambda w, _: (setattr(opt_bg, "pos", w.pos),
                              setattr(opt_brd, "rounded_rectangle",
                                      [w.x, w.y, w.width, w.height, dp(14)])),
            size=lambda w, _: (setattr(opt_bg, "size", w.size),
                               setattr(opt_brd, "rounded_rectangle",
                                       [w.x, w.y, w.width, w.height, dp(14)])),
        )
        dot2 = Widget(size_hint=(None, None), size=(dp(6), dp(6)))
        with dot2.canvas:
            Color(*PRIMARY)
            Ellipse(pos=dot2.pos, size=dot2.size)
        dot2.bind(pos=lambda w, _: w.canvas.clear() or self._dot2_draw(w),
                  size=lambda w, _: w.canvas.clear() or self._dot2_draw(w))
        opt_chip.add_widget(dot2)
        opt_chip.add_widget(Label(text="OPTIMAL", font_size=sp(9), bold=True, color=PRIMARY))
        bpm_top.add_widget(opt_chip)
        bpm_card.add_widget(bpm_top)

        # Bar chart
        chart_days = stats["daily_bpm"]
        chart = BPMBarChart(size_hint_y=None, height=dp(150))
        chart.data = chart_days
        bpm_card.add_widget(chart)

        # Day labels
        day_row = BoxLayout(size_hint_y=None, height=dp(18))
        for label, _, _ in chart_days:
            day_row.add_widget(Label(
                text=label, font_size=sp(10), color=ON_VARIANT,
            ))
        bpm_card.add_widget(day_row)
        c.add_widget(bpm_card)

        # HR Range card
        range_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(110),
            padding=[dp(16), dp(12)], spacing=dp(8),
        )
        draw_card(range_card, CARD, radius=14)
        range_card.add_widget(Label(
            text="HEART RATE RANGE", font_size=sp(10), bold=True,
            color=ON_VARIANT, halign="left", size_hint_y=None, height=dp(18),
        ))
        minmax = GridLayout(cols=2, size_hint_y=None, height=dp(40))
        for lbl, val in [("MIN", str(stats["min_bpm"])), ("MAX", str(stats["max_bpm"]))]:
            box = BoxLayout(orientation="vertical")
            box.add_widget(Label(text=lbl, font_size=sp(10), color=(*OUTLINE[:3], 0.7),
                                 halign="left", size_hint_y=None, height=dp(14)))
            box.add_widget(Label(text=val, font_size=sp(26), bold=True,
                                 color=ON_SURFACE, halign="left",
                                 size_hint_y=None, height=dp(36)))
            minmax.add_widget(box)
        range_card.add_widget(minmax)

        # Range bar
        range_bar = Widget(size_hint_y=None, height=dp(6))
        with range_bar.canvas:
            Color(*CARD_HIGHEST)
            RoundedRectangle(pos=range_bar.pos, size=range_bar.size, radius=[dp(3)])
            Color(*PRIMARY_C[:3], 0.4)
            RoundedRectangle(pos=range_bar.pos,
                             size=(range_bar.width * 0.3, range_bar.height), radius=[dp(3)])
            Color(*PRIMARY_C)
            RoundedRectangle(
                pos=(range_bar.x + range_bar.width * 0.3, range_bar.y),
                size=(range_bar.width * 0.4, range_bar.height), radius=[dp(3)])
        range_card.add_widget(range_bar)
        c.add_widget(range_card)

        # Avg HRV card
        hrv_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(100),
            padding=[dp(16), dp(12)], spacing=dp(6),
        )
        with hrv_card.canvas.before:
            Color(*CARD)
            hrv_bg = RoundedRectangle(pos=hrv_card.pos, size=hrv_card.size, radius=[dp(14)])
            Color(*PRIMARY_C[:3], 0.8)
            hrv_lb = Line(
                points=[hrv_card.x, hrv_card.y + dp(14),
                        hrv_card.x, hrv_card.top - dp(14)],
                width=dp(2),
            )
            Color(1, 1, 1, 0.08)
            hrv_brd = Line(
                rounded_rectangle=[hrv_card.x, hrv_card.y, hrv_card.width, hrv_card.height, dp(14)],
                width=0.8,
            )
        hrv_card.bind(
            pos=lambda w, _: (setattr(hrv_bg, "pos", w.pos),
                              setattr(hrv_lb, "points",
                                      [w.x, w.y + dp(14), w.x, w.top - dp(14)]),
                              setattr(hrv_brd, "rounded_rectangle",
                                      [w.x, w.y, w.width, w.height, dp(14)])),
            size=lambda w, _: (setattr(hrv_bg, "size", w.size),
                               setattr(hrv_lb, "points",
                                       [w.x, w.y + dp(14), w.x, w.top - dp(14)]),
                               setattr(hrv_brd, "rounded_rectangle",
                                       [w.x, w.y, w.width, w.height, dp(14)])),
        )
        hrv_card.add_widget(Label(
            text="AVG HRV", font_size=sp(10), bold=True, color=ON_VARIANT,
            halign="left", size_hint_y=None, height=dp(18),
        ))
        hrv_val_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        hrv_val_row.add_widget(Label(
            text=str(stats["avg_hrv"]), font_size=sp(30), bold=True,
            color=ON_SURFACE, halign="left",
        ))
        hrv_val_row.add_widget(Label(text="ms", font_size=sp(16), color=ON_VARIANT))
        hrv_card.add_widget(hrv_val_row)
        hrv_card.add_widget(Label(
            text="^ Stable Baseline", font_size=sp(12), color=(*PRIMARY[:3], 0.8),
            halign="left", size_hint_y=None, height=dp(20),
        ))
        c.add_widget(hrv_card)

        # Circadian Sync card
        circ_card = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(120),
            padding=[dp(16), dp(16)], spacing=dp(16),
        )
        draw_card(circ_card, CARD, radius=14)

        icon_circle = Widget(size_hint=(None, None), size=(dp(60), dp(60)))
        with icon_circle.canvas:
            Color(*PRIMARY_C[:3], 0.12)
            Ellipse(pos=icon_circle.pos, size=icon_circle.size)
            Color(*PRIMARY_C[:3], 0.3)
            Line(circle=(icon_circle.center_x, icon_circle.center_y, dp(29)), width=dp(1.2))

        def _redraw_ic(w, _=None):
            w.canvas.clear()
            cx, cy = w.center_x, w.center_y
            with w.canvas:
                Color(*PRIMARY_C[:3], 0.12)
                Ellipse(pos=w.pos, size=w.size)
                Color(*PRIMARY_C[:3], 0.3)
                Line(circle=(cx, cy, dp(29)), width=dp(1.2))
                Color(*PRIMARY_C)
                Line(points=[cx, cy, cx, cy + dp(20)], width=dp(1.5), cap="round")
                Line(points=[cx, cy, cx + dp(14), cy], width=dp(1.5), cap="round")

        icon_circle.bind(pos=_redraw_ic, size=_redraw_ic)
        circ_card.add_widget(icon_circle)

        circ_text = BoxLayout(orientation="vertical", spacing=dp(4))
        circ_text.add_widget(Label(
            text="Circadian Sync", font_size=sp(18), bold=True,
            color=ON_SURFACE, halign="left", size_hint_y=None, height=dp(28),
        ))
        circ_body = Label(
            text="Your heart rate dips peaked at 3:15 AM, indicating a deep recovery cycle.",
            font_size=sp(13), color=ON_VARIANT, halign="left",
        )
        circ_body.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        circ_text.add_widget(circ_body)
        circ_text.add_widget(Label(
            text="VIEW FULL REPORT  >", font_size=sp(11), color=PRIMARY,
            halign="left", size_hint_y=None, height=dp(20),
        ))
        circ_card.add_widget(circ_text)
        c.add_widget(circ_card)

        # Recovery score card
        rec_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(130),
            padding=[dp(16), dp(14)], spacing=dp(6),
        )
        with rec_card.canvas.before:
            Color(*CARD)
            rec_bg = RoundedRectangle(pos=rec_card.pos, size=rec_card.size, radius=[dp(14)])
            # Decoration glow
            Color(*PRIMARY_C[:3], 0.08)
            rec_glow = Ellipse(
                pos=(rec_card.right - dp(60), rec_card.y - dp(20)),
                size=(dp(120), dp(120)),
            )
            Color(1, 1, 1, 0.08)
            rec_brd = Line(
                rounded_rectangle=[rec_card.x, rec_card.y, rec_card.width, rec_card.height, dp(14)],
                width=0.8,
            )
        rec_card.bind(
            pos=lambda w, _: (setattr(rec_bg, "pos", w.pos),
                              setattr(rec_glow, "pos", (w.right - dp(60), w.y - dp(20))),
                              setattr(rec_brd, "rounded_rectangle",
                                      [w.x, w.y, w.width, w.height, dp(14)])),
            size=lambda w, _: (setattr(rec_bg, "size", w.size),
                               setattr(rec_glow, "pos", (w.right - dp(60), w.y - dp(20))),
                               setattr(rec_brd, "rounded_rectangle",
                                       [w.x, w.y, w.width, w.height, dp(14)])),
        )

        rec_card.add_widget(Label(
            text="RECOVERY SCORE", font_size=sp(10), bold=True,
            color=ON_VARIANT, halign="left", size_hint_y=None, height=dp(18),
        ))
        rec_num_row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(12))
        rec_num_row.add_widget(Label(
            text="82%", font_size=sp(44), bold=True,
            color=ON_SURFACE, halign="left", size_hint_x=None, width=dp(110),
        ))
        plus_chip = BoxLayout(
            size_hint=(None, None), size=(dp(60), dp(26)),
            padding=[dp(8), dp(4)], spacing=dp(4),
        )
        with plus_chip.canvas.before:
            Color(*PRIMARY[:3], 0.18)
            RoundedRectangle(pos=plus_chip.pos, size=plus_chip.size, radius=[dp(13)])
        plus_chip.bind(
            pos=lambda w, _: w.canvas.before.clear() or _draw_plus_chip(w),
            size=lambda w, _: w.canvas.before.clear() or _draw_plus_chip(w),
        )
        plus_chip.add_widget(Label(text="+", font_size=sp(12), bold=True, color=PRIMARY,
                                   size_hint_x=None, width=dp(10)))
        plus_chip.add_widget(Label(text="5%", font_size=sp(11), bold=True, color=PRIMARY))
        rec_num_row.add_widget(plus_chip)
        rec_card.add_widget(rec_num_row)
        rec_card.add_widget(Label(
            text="v last week", font_size=sp(11), color=(*OUTLINE[:3], 0.7),
            halign="left", size_hint_y=None, height=dp(18),
        ))
        rec_card.add_widget(Label(
            text='"Ready for high-intensity training today."',
            font_size=sp(13), color=ON_VARIANT,
            halign="left", size_hint_y=None, height=dp(22),
        ))
        c.add_widget(rec_card)

    def _dot2_draw(self, w):
        with w.canvas:
            Color(*PRIMARY)
            Ellipse(pos=w.pos, size=w.size)

    def _compute_stats(self):
        log = load_log()
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        week = [e for e in log if self._ts_ok(e.get("ts"), week_ago)]
        bpms = [e["bpm"] for e in week if e.get("bpm")]
        hrvs = [e["rmssd"] for e in week if e.get("rmssd")]

        # Daily BPM for chart
        days = []
        day_labels = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
        today_dow = now.weekday()  # 0=Mon
        for i in range(7):
            offset = (i - today_dow) % 7
            d = now - timedelta(days=6-i)
            day_bpms = [e["bpm"] for e in log
                        if self._ts_ok(e.get("ts"), d - timedelta(hours=12))
                        and e.get("bpm")]
            val = round(sum(day_bpms)/len(day_bpms)) if day_bpms else random.randint(65, 85)
            is_today = (i == 6)
            days.append((day_labels[d.weekday()], val, is_today))

        return {
            "avg_bpm":  round(sum(bpms)/len(bpms)) if bpms else 72,
            "max_bpm":  max(bpms) if bpms else 142,
            "min_bpm":  min(bpms) if bpms else 58,
            "avg_hrv":  round(sum(hrvs)/len(hrvs)) if hrvs else 64,
            "daily_bpm": days,
        }

    def _ts_ok(self, ts, after):
        try:
            return datetime.fromisoformat(ts) >= after
        except Exception:
            return False


def _draw_plus_chip(w):
    with w.canvas.before:
        Color(*PRIMARY[:3], 0.18)
        RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(13)])


# ── DevTools Screen ────────────────────────────────────────────────────────────

class DevToolsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        draw_bg(root)

        col = BoxLayout(orientation="vertical", size_hint=(1, 1))
        col.add_widget(TopBar())

        sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        c = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(12), dp(20), dp(16)],
            spacing=dp(16), size_hint_y=None,
        )
        c.bind(minimum_height=c.setter("height"))

        # Title
        c.add_widget(Label(
            text="DevTools", font_size=sp(32), bold=True,
            color=PRIMARY_C, size_hint_y=None, height=dp(48), halign="left",
        ))
        c.add_widget(Label(
            text="Internal pacing engine diagnostics and\nhardware simulation suite.",
            font_size=sp(14), color=ON_VARIANT,
            size_hint_y=None, height=dp(44), halign="left",
        ))

        # System Diagnostics card
        diag_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(200),
            padding=[dp(16), dp(14)], spacing=dp(8),
        )
        draw_card(diag_card, CARD, radius=14)

        diag_hdr = BoxLayout(size_hint_y=None, height=dp(30))
        diag_hdr.add_widget(Label(
            text="System Diagnostics", font_size=sp(18), bold=True,
            color=PRIMARY_C, halign="left",
        ))
        active_chip = BoxLayout(size_hint=(None, None), size=(dp(72), dp(24)),
                                padding=[dp(8), dp(4)], spacing=dp(4))
        with active_chip.canvas.before:
            Color(*GREEN[:3], 0.15)
            RoundedRectangle(pos=active_chip.pos, size=active_chip.size, radius=[dp(12)])
        active_chip.bind(
            pos=lambda w, _: w.canvas.before.clear() or self._draw_active(w),
            size=lambda w, _: w.canvas.before.clear() or self._draw_active(w),
        )
        a_dot = Widget(size_hint=(None, None), size=(dp(6), dp(6)))
        with a_dot.canvas:
            Color(*GREEN)
            Ellipse(pos=a_dot.pos, size=a_dot.size)
        a_dot.bind(pos=lambda w, _: w.canvas.clear() or self._draw_green_dot(w),
                   size=lambda w, _: w.canvas.clear() or self._draw_green_dot(w))
        active_chip.add_widget(a_dot)
        active_chip.add_widget(Label(text="ACTIVE", font_size=sp(9), bold=True, color=GREEN))
        diag_hdr.add_widget(active_chip)
        diag_card.add_widget(diag_hdr)

        diag_card.add_widget(Label(
            text="Real-time kernel monitoring and sensor health status.",
            font_size=sp(12), color=ON_VARIANT,
            size_hint_y=None, height=dp(32), halign="left",
        ))

        for label, val in [
            ("Kernel Sync Frequency", "1.2ms avg"),
            ("Memory Footprint",      "142MB / 2.0GB"),
            ("Hardware Handshake",    "Verified (v4.2)"),
        ]:
            row = BoxLayout(size_hint_y=None, height=dp(36),
                            padding=[dp(10), dp(4)])
            draw_card(row, CARD_HIGH, radius=6)
            row.add_widget(Label(text=label, font_size=sp(13), color=ON_VARIANT,
                                 halign="left"))
            row.add_widget(Label(text=val, font_size=sp(13), color=ON_SURFACE,
                                 halign="right"))
            diag_card.add_widget(row)
            diag_card.add_widget(Widget(size_hint_y=None, height=dp(2)))

        c.add_widget(diag_card)

        # Quick Controls card
        ctrl_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(130),
            padding=[dp(16), dp(12)], spacing=dp(10),
        )
        draw_card(ctrl_card, CARD, radius=14)
        ctrl_card.add_widget(Label(
            text="QUICK CONTROLS", font_size=sp(10), bold=True,
            color=ON_VARIANT, halign="left", size_hint_y=None, height=dp(18),
        ))

        self._sim_toggle = ToggleSwitch(active=USE_SIMULATOR)
        self._dev_toggle = ToggleSwitch(active=False)

        for lbl_text, sub_text, toggle in [
            ("Simulator Mode",  "Inject mock ECG data",      self._sim_toggle),
            ("Developer Mode",  "Expose hidden API routes",  self._dev_toggle),
        ]:
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
            txt_col = BoxLayout(orientation="vertical")
            txt_col.add_widget(Label(text=lbl_text, font_size=sp(14), bold=True,
                                     color=ON_SURFACE, halign="left",
                                     size_hint_y=None, height=dp(22)))
            txt_col.add_widget(Label(text=sub_text, font_size=sp(11),
                                     color=ON_VARIANT, halign="left",
                                     size_hint_y=None, height=dp(18)))
            row.add_widget(txt_col)
            row.add_widget(toggle)
            ctrl_card.add_widget(row)
        c.add_widget(ctrl_card)

        # Live Telemetry
        c.add_widget(Label(
            text="LIVE TELEMETRY", font_size=sp(10), bold=True,
            color=ON_VARIANT, halign="left", size_hint_y=None, height=dp(18),
        ))
        tele_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(130))
        self._t_hr     = StatChip(icon="♥", label="HR",      value="72", unit="BPM", bar=0.5)
        self._t_o2     = StatChip(icon="o", label="O2 SAT",  value="98", unit="%",   bar=0.98)
        self._t_cad    = StatChip(icon="r", label="CADENCE", value="164",unit="SPM", bar=0.82)
        self._t_lat    = StatChip(icon="*", label="LATENCY", value="24", unit="MS",  bar=0.12)
        tele_grid.add_widget(self._t_hr)
        tele_grid.add_widget(self._t_o2)
        tele_grid.add_widget(self._t_cad)
        tele_grid.add_widget(self._t_lat)
        c.add_widget(tele_grid)

        # Telemetry bar chart
        tele_chart = BPMBarChart(size_hint_y=None, height=dp(90))
        tele_chart.data = [
            ("", 40, False), ("", 65, False), ("", 55, False),
            ("", 80, True),  ("", 70, False), ("", 85, False),
            ("", 60, False), ("", 75, False), ("", 50, False),
            ("", 90, True),  ("", 65, False), ("", 45, False),
        ]
        wrap = BoxLayout(size_hint_y=None, height=dp(90), padding=[dp(0), 0])
        draw_card(wrap, CARD, radius=10)
        wrap.add_widget(tele_chart)
        c.add_widget(wrap)

        # Buffer Overrides
        buf_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(130),
            padding=[dp(16), dp(12)], spacing=dp(8),
        )
        draw_card(buf_card, CARD, radius=14)
        buf_card.add_widget(Label(
            text="Buffer Overrides", font_size=sp(20), bold=True,
            color=PRIMARY_C, halign="left", size_hint_y=None, height=dp(30),
        ))

        sr_lbl = Label(text="SAMPLING RATE", font_size=sp(10), bold=True,
                       color=ON_VARIANT, halign="left", size_hint_y=None, height=dp(18))
        buf_card.add_widget(sr_lbl)
        sr_row = BoxLayout(size_hint_y=None, height=dp(32))
        sr_slider = Slider(min=256, max=1024, value=512, size_hint_x=0.8,
                           cursor_size=(dp(18), dp(18)))
        self._sr_lbl = Label(text="512 HZ", font_size=sp(12), bold=True,
                             color=PRIMARY, size_hint_x=None, width=dp(70))
        sr_slider.bind(value=lambda i, v: setattr(self._sr_lbl, "text", f"{int(v)} HZ"))
        sr_row.add_widget(sr_slider)
        sr_row.add_widget(self._sr_lbl)
        buf_card.add_widget(sr_row)

        lat_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(10))
        lat_row.add_widget(Label(text="LATENCY BUFFER", font_size=sp(10), bold=True,
                                 color=ON_VARIANT, halign="left",
                                 size_hint_y=None, height=dp(18)))
        lat_val = BoxLayout(size_hint=(None, 1), width=dp(100),
                            padding=[dp(8), dp(4)])
        draw_card(lat_val, CARD_HIGH, radius=6)
        lat_val.add_widget(Label(text="128kb", font_size=sp(13), color=ON_SURFACE))
        lat_row.add_widget(lat_val)
        lat_row.add_widget(Label(text="STATIC_VAL", font_size=sp(10),
                                 color=ON_VARIANT, halign="right"))
        buf_card.add_widget(lat_row)
        c.add_widget(buf_card)

        # Stress Test Scenarios
        stress_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(220),
            padding=[dp(16), dp(14)], spacing=dp(10),
        )
        draw_card(stress_card, CARD, radius=14)
        stress_card.add_widget(Label(
            text="Stress Test Scenarios", font_size=sp(20), bold=True,
            color=PRIMARY_C, halign="left", size_hint_y=None, height=dp(30),
        ))

        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(140))
        sc_map = [
            ("resting",    "♥ RESTING",    False),
            ("walking",    "^ WALKING",    False),
            ("pots_spike", "♥ POTS SPIKE", True),
            ("running",    "/ RUNNING",    False),
        ]
        self._sc_btns = []
        for key, label, active in sc_map:
            chip = ScenarioChip(text=label, active=active)
            chip._sc_key = key
            chip.bind(on_release=self._run_scenario)
            self._sc_btns.append(chip)
            grid.add_widget(chip)
        stress_card.add_widget(grid)

        recovery_chip = ScenarioChip(text="* RECOVERY", active=False)
        recovery_chip._sc_key = "recovery"
        recovery_chip.bind(on_release=self._run_scenario)
        self._sc_btns.append(recovery_chip)
        stress_card.add_widget(recovery_chip)
        c.add_widget(stress_card)

        sv.add_widget(c)
        col.add_widget(sv)
        col.add_widget(BottomNav(active="devtools", on_navigate=lambda k: _nav(self.manager, k)))
        root.add_widget(col)
        self.add_widget(root)

    def _draw_active(self, w):
        with w.canvas.before:
            Color(*GREEN[:3], 0.15)
            RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(12)])

    def _draw_green_dot(self, w):
        with w.canvas:
            Color(*GREEN)
            Ellipse(pos=w.pos, size=w.size)

    def _run_scenario(self, btn):
        sc = btn._sc_key
        global USE_SIMULATOR
        USE_SIMULATOR = True
        self._sim_toggle.active = True
        monitor = App.get_running_app().root.get_screen("monitor")
        monitor._start_sim(sc)
        _nav(self.manager, "monitor")


# ── Profile Screen ─────────────────────────────────────────────────────────────

class ProfileScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        draw_bg(root)

        col = BoxLayout(orientation="vertical", size_hint=(1, 1))
        col.add_widget(TopBar())

        sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        c = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(16), dp(20), dp(20)],
            spacing=dp(16), size_hint_y=None,
        )
        c.bind(minimum_height=c.setter("height"))

        # Avatar section
        avatar_section = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(130),
            spacing=dp(8),
        )
        avatar_outer = FloatLayout(size_hint_y=None, height=dp(90))
        avatar_circle = Widget(
            size_hint=(None, None), size=(dp(80), dp(80)),
            pos_hint={"center_x": 0.5, "top": 1.0},
        )
        with avatar_circle.canvas:
            Color(*PRIMARY_C, 1.0)
            Line(circle=(dp(40), dp(40), dp(39)), width=dp(1.8))
            Color(*CARD_HIGH)
            Ellipse(pos=(dp(2), dp(2)), size=(dp(76), dp(76)))
            Color(*PRIMARY_C[:3], 0.4)
            Ellipse(pos=(dp(2), dp(2)), size=(dp(76), dp(76)))

        def _redraw_av(w, _=None):
            w.canvas.clear()
            cx, cy = w.center_x - w.x, w.center_y - w.y
            r = min(w.width, w.height) / 2 - dp(1)
            with w.canvas:
                Color(*PRIMARY_C)
                Line(circle=(cx, cy, r), width=dp(1.8))
                Color(*CARD_HIGH)
                Ellipse(pos=(w.x + dp(2), w.y + dp(2)),
                        size=(w.width - dp(4), w.height - dp(4)))

        avatar_circle.bind(pos=_redraw_av, size=_redraw_av)

        # Edit button
        edit_btn = Widget(
            size_hint=(None, None), size=(dp(24), dp(24)),
            pos_hint={"center_x": 0.62, "y": 0.0},
        )
        with edit_btn.canvas:
            Color(*PRIMARY_C)
            Ellipse(pos=edit_btn.pos, size=edit_btn.size)

        def _redraw_edit(w, _=None):
            w.canvas.clear()
            with w.canvas:
                Color(*PRIMARY_C)
                Ellipse(pos=w.pos, size=w.size)

        edit_btn.bind(pos=_redraw_edit, size=_redraw_edit)

        avatar_outer.add_widget(avatar_circle)
        avatar_outer.add_widget(edit_btn)
        avatar_section.add_widget(avatar_outer)

        p = App.get_running_app().profile
        name = p.get("name", "Ryan")
        avatar_section.add_widget(Label(
            text=name, font_size=sp(24), bold=True,
            color=ON_SURFACE, size_hint_y=None, height=dp(32),
        ))
        avatar_section.add_widget(Label(
            text="Elite Tier Member", font_size=sp(14),
            color=ON_VARIANT, size_hint_y=None, height=dp(20),
        ))
        c.add_widget(avatar_section)

        # Personal Metrics card
        metrics_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(240),
            padding=[dp(16), dp(14)], spacing=dp(10),
        )
        draw_card(metrics_card, CARD, radius=14)
        metrics_card.add_widget(Label(
            text="Personal Metrics", font_size=sp(18), bold=True,
            color=PRIMARY_C, halign="left", size_hint_y=None, height=dp(28),
        ))

        # Display Name field
        metrics_card.add_widget(Label(
            text="Display Name", font_size=sp(11), bold=True,
            color=ON_VARIANT, halign="left", size_hint_y=None, height=dp(18),
        ))
        name_inp = TextInput(
            text=name,
            foreground_color=ON_SURFACE, background_color=CARD_HIGH,
            cursor_color=PRIMARY_C,
            font_size=sp(15), padding=[dp(12), dp(10)],
            size_hint_y=None, height=dp(44), multiline=False,
        )
        metrics_card.add_widget(name_inp)

        # HR + Weight row
        hw_row = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(12))
        for lbl, val, unit in [("Resting Heart Rate", "54", "BPM"),
                                ("Weight Class", "72 kg", "")]:
            box = BoxLayout(orientation="vertical", spacing=dp(4))
            box.add_widget(Label(text=lbl, font_size=sp(11), bold=True,
                                 color=ON_VARIANT, halign="left",
                                 size_hint_y=None, height=dp(18)))
            inp_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            inp = TextInput(
                text=val,
                foreground_color=ON_SURFACE, background_color=CARD_HIGH,
                cursor_color=PRIMARY_C,
                font_size=sp(15), padding=[dp(10), dp(10)],
                size_hint_y=None, height=dp(44), multiline=False,
            )
            inp_row.add_widget(inp)
            if unit:
                inp_row.add_widget(Label(text=unit, font_size=sp(13),
                                         color=ON_VARIANT, size_hint=(None, 1), width=dp(36)))
            box.add_widget(inp_row)
            hw_row.add_widget(box)
        metrics_card.add_widget(hw_row)

        # Sensitivity selector
        metrics_card.add_widget(Label(
            text="Sensitivity Level", font_size=sp(11), bold=True,
            color=ON_VARIANT, halign="left", size_hint_y=None, height=dp(18),
        ))
        sens_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(0))
        with sens_row.canvas.before:
            Color(*CARD_HIGH)
            sr_bg = RoundedRectangle(pos=sens_row.pos, size=sens_row.size, radius=[dp(10)])
            Color(*OUTLINE_VAR, 0.3)
            sr_brd = Line(
                rounded_rectangle=[sens_row.x, sens_row.y, sens_row.width, sens_row.height, dp(10)],
                width=0.8,
            )
        sens_row.bind(
            pos=lambda w, _: (setattr(sr_bg, "pos", w.pos),
                              setattr(sr_brd, "rounded_rectangle",
                                      [w.x, w.y, w.width, w.height, dp(10)])),
            size=lambda w, _: (setattr(sr_bg, "size", w.size),
                               setattr(sr_brd, "rounded_rectangle",
                                       [w.x, w.y, w.width, w.height, dp(10)])),
        )
        for opt in ["Low", "Medium", "High"]:
            active = opt == "Medium"
            sb = Button(
                text=opt, font_size=sp(13), bold=True,
                color=ON_PRIMARY if active else ON_VARIANT,
                background_normal="", background_color=[0,0,0,0],
            )
            if active:
                with sb.canvas.before:
                    Color(*PRIMARY_C)
                    sb_bg = RoundedRectangle(pos=sb.pos, size=sb.size, radius=[dp(8)])
                sb.bind(
                    pos=lambda w, _, bg=sb_bg: setattr(bg, "pos", w.pos),
                    size=lambda w, _, bg=sb_bg: setattr(bg, "size", w.size),
                )
            sens_row.add_widget(sb)
        metrics_card.add_widget(sens_row)
        c.add_widget(metrics_card)

        # Connectivity card
        conn_card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(150),
            padding=[dp(16), dp(14)], spacing=dp(10),
        )
        draw_card(conn_card, CARD, radius=14)

        band_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(12))
        band_icon = Widget(size_hint=(None, None), size=(dp(36), dp(36)))
        with band_icon.canvas:
            Color(*PRIMARY_C[:3], 0.18)
            RoundedRectangle(pos=band_icon.pos, size=band_icon.size, radius=[dp(8)])
        band_icon.bind(
            pos=lambda w, _: w.canvas.clear() or self._redraw_band_icon(w),
            size=lambda w, _: w.canvas.clear() or self._redraw_band_icon(w),
        )
        band_row.add_widget(band_icon)

        band_info = BoxLayout(orientation="vertical")
        band_info.add_widget(Label(
            text="Xiaomi Band 10", font_size=sp(15), bold=True,
            color=ON_SURFACE, halign="left", size_hint_y=None, height=dp(24),
        ))
        conn_status = BoxLayout(size_hint_y=None, height=dp(18), spacing=dp(6))
        conn_dot = Widget(size_hint=(None, None), size=(dp(8), dp(8)))
        with conn_dot.canvas:
            Color(*GREEN)
            Ellipse(pos=conn_dot.pos, size=conn_dot.size)
        conn_dot.bind(
            pos=lambda w, _: w.canvas.clear() or self._draw_green_dot2(w),
            size=lambda w, _: w.canvas.clear() or self._draw_green_dot2(w),
        )
        conn_status.add_widget(conn_dot)
        conn_status.add_widget(Label(text="Connected", font_size=sp(11), color=GREEN,
                                      halign="left"))
        band_info.add_widget(conn_status)
        band_row.add_widget(band_info)

        switch_btn = Button(
            text="Switch", font_size=sp(12), bold=True,
            color=PRIMARY, background_normal="", background_color=[0,0,0,0],
            size_hint=(None, None), size=(dp(70), dp(30)),
        )
        with switch_btn.canvas.before:
            Color(*PRIMARY_C[:3], 0.15)
            switch_bg = RoundedRectangle(pos=switch_btn.pos, size=switch_btn.size, radius=[dp(15)])
            Color(*PRIMARY_C, 0.3)
            switch_brd = Line(
                rounded_rectangle=[switch_btn.x, switch_btn.y,
                                    switch_btn.width, switch_btn.height, dp(15)],
                width=0.8,
            )
        switch_btn.bind(
            pos=lambda w, _, bg=switch_bg, brd=switch_brd: (
                setattr(bg, "pos", w.pos),
                setattr(brd, "rounded_rectangle", [w.x, w.y, w.width, w.height, dp(15)])
            ),
            size=lambda w, _, bg=switch_bg, brd=switch_brd: (
                setattr(bg, "size", w.size),
                setattr(brd, "rounded_rectangle", [w.x, w.y, w.width, w.height, dp(15)])
            ),
        )
        band_row.add_widget(switch_btn)
        conn_card.add_widget(band_row)

        for icon, label, toggle_active in [
            ("*", "Activity Alerts",  True),
            ("~", "Haptic Feedback",  False),
        ]:
            tr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(12))
            tr.add_widget(Label(text=icon, font_size=sp(16), color=ON_VARIANT,
                                size_hint=(None, 1), width=dp(26)))
            tr.add_widget(Label(text=label, font_size=sp(14), color=ON_SURFACE,
                                halign="left"))
            tog = ToggleSwitch(active=toggle_active)
            tr.add_widget(tog)
            conn_card.add_widget(tr)
        c.add_widget(conn_card)

        # Settings rows
        for icon, label in [("O", "Privacy & Security"), ("?", "Support Center")]:
            row = BoxLayout(size_hint_y=None, height=dp(56),
                            padding=[dp(16), 0], spacing=dp(12))
            draw_card(row, CARD, radius=12)
            row.add_widget(Label(text=icon, font_size=sp(16), color=ON_VARIANT,
                                 size_hint=(None, 1), width=dp(28)))
            lbl = Label(text=label, font_size=sp(14), color=ON_SURFACE,
                        halign="left", valign="middle")
            lbl.bind(size=lambda w, _: setattr(w, "text_size", w.size))
            row.add_widget(lbl)
            row.add_widget(Label(text=">", font_size=sp(16), color=ON_VARIANT,
                                 size_hint=(None, 1), width=dp(28)))
            c.add_widget(row)

        # Logout button
        logout_btn = Button(
            text="Log Out", font_size=sp(17), bold=True,
            color=ERROR,
            background_normal="", background_color=[0,0,0,0],
            size_hint_y=None, height=dp(56),
        )
        with logout_btn.canvas.before:
            Color(*ERROR[:3], 0.08)
            lg_bg = RoundedRectangle(pos=logout_btn.pos, size=logout_btn.size, radius=[dp(14)])
            Color(*ERROR[:3], 0.3)
            lg_brd = Line(
                rounded_rectangle=[logout_btn.x, logout_btn.y,
                                    logout_btn.width, logout_btn.height, dp(14)],
                width=0.8,
            )
        logout_btn.bind(
            pos=lambda w, _, bg=lg_bg, brd=lg_brd: (
                setattr(bg, "pos", w.pos),
                setattr(brd, "rounded_rectangle", [w.x, w.y, w.width, w.height, dp(14)])
            ),
            size=lambda w, _, bg=lg_bg, brd=lg_brd: (
                setattr(bg, "size", w.size),
                setattr(brd, "rounded_rectangle", [w.x, w.y, w.width, w.height, dp(14)])
            ),
        )
        c.add_widget(logout_btn)

        c.add_widget(Label(
            text=f"Version {APP_VERSION} (Build {APP_BUILD})",
            font_size=sp(11), color=(*ON_VARIANT[:3], 0.4),
            size_hint_y=None, height=dp(24),
        ))

        sv.add_widget(c)
        col.add_widget(sv)
        col.add_widget(BottomNav(active="profile", on_navigate=lambda k: _nav(self.manager, k)))
        root.add_widget(col)
        self.add_widget(root)

    def _redraw_band_icon(self, w):
        with w.canvas:
            Color(*PRIMARY_C[:3], 0.18)
            RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(8)])

    def _draw_green_dot2(self, w):
        with w.canvas:
            Color(*GREEN)
            Ellipse(pos=w.pos, size=w.size)


# ── App ────────────────────────────────────────────────────────────────────────

class PaceRingApp(App):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.profile = {
            "name": "Ryan", "resting_bpm": 65, "threshold": 110,
            "spike_delta": 30, "spike_duration": 10,
            "vibration": True, "sound_alerts": True,
        }

    def build(self):
        Window.clearcolor = BG
        saved = load_profile()
        if saved:
            self.profile.update(saved)

        sm = ScreenManager(transition=FadeTransition(duration=0.12))
        sm.add_widget(OnboardScreen1(name="onboard"))
        sm.add_widget(MonitorScreen(name="monitor"))
        sm.add_widget(SummaryScreen(name="summary"))
        sm.add_widget(DevToolsScreen(name="devtools"))
        sm.add_widget(ProfileScreen(name="profile"))

        if saved and saved.get("name"):
            sm.current = "monitor"
            Clock.schedule_once(
                lambda dt: sm.get_screen("monitor").start_monitoring(), 0.5
            )
        else:
            sm.current = "onboard"

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
