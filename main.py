cat > /mnt/user-data/outputs/main.py << 'ENDOFFILE'
"""
PaceRing v3.0 — Complete rebuilt UI
Deep purple health monitoring app for POTS management
"""

import json
import os
import math
import random
from datetime import datetime
from collections import deque
from typing import Optional

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse, Rectangle
from kivy.animation import Animation
from kivy.metrics import dp, sp

USE_SIMULATOR = True

if USE_SIMULATOR:
    from fake_ble import FakeBLEWorker as BLEWorker
else:
    from real_ble import RealBLEWorker as BLEWorker

from alert_engine import AlertEngine, AlertConfig, AlertEvent

# ── Palette ───────────────────────────────────────────────────────────────────
BG         = (0.063, 0.051, 0.102, 1)    # #100d1a
SURFACE    = (0.11,  0.09,  0.18,  1)    # card surface
SURFACE2   = (0.16,  0.13,  0.25,  1)    # elevated surface
PURPLE     = (0.42,  0.17,  0.91,  1)    # #6c2bea
PURPLE2    = (0.31,  0.10,  0.67,  1)    # darker purple
FUCHSIA    = (0.91,  0.475, 0.976, 1)    # #e879f9
RED        = (0.957, 0.247, 0.369, 1)    # #f43f5e
AMBER      = (0.96,  0.62,  0.04,  1)    # warning amber
GREEN      = (0.30,  0.89,  0.40,  1)    # clear/safe
WHITE      = (0.93,  0.91,  0.99,  1)    # near white
MUTED      = (0.42,  0.37,  0.62,  1)    # muted text
MUTED2     = (0.27,  0.23,  0.40,  1)    # very muted

PROFILE_FILE = "pacering_profile.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def save_profile(data: dict):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f)


def load_profile() -> Optional[dict]:
    if os.path.exists(PROFILE_FILE):
        try:
            return json.load(open(PROFILE_FILE))
        except Exception:
            pass
    return None


def time_greeting(name: str) -> str:
    h = datetime.now().hour
    if 6 <= h < 12:   prefix = "good morning"
    elif 12 <= h < 17: prefix = "good afternoon"
    elif 17 <= h < 21: prefix = "good evening"
    else:              prefix = "hey, rest up"
    return f"{prefix}, {name.lower()}"


def paint_bg(widget, color=None, radius=16):
    """Attach a responsive rounded background to any widget."""
    color = color or SURFACE
    with widget.canvas.before:
        col = Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])

    def _update(*_):
        rect.pos  = widget.pos
        rect.size = widget.size

    widget.bind(pos=_update, size=_update)
    return rect, col


# ── Reusable widgets ──────────────────────────────────────────────────────────

class PillLabel(BoxLayout):
    """Small pill-shaped label with colored background."""
    def __init__(self, text, bg=SURFACE2, text_color=MUTED, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(120), dp(28)), **kwargs)
        paint_bg(self, bg, radius=14)
        self.lbl = Label(text=text, font_size=sp(12), color=text_color)
        self.add_widget(self.lbl)

    def set_text(self, text, color=None):
        self.lbl.text = text
        if color:
            self.lbl.color = color


class StatCard(BoxLayout):
    def __init__(self, title, value, unit="", **kwargs):
        super().__init__(orientation="vertical", padding=[dp(12), dp(10)], **kwargs)
        paint_bg(self, SURFACE, radius=14)

        self.val_lbl = Label(
            text=value, font_size=sp(20), bold=True, color=WHITE,
            size_hint_y=None, height=dp(32),
        )
        self.title_lbl = Label(
            text=f"{title}" + (f"  {unit}" if unit else ""),
            font_size=sp(11), color=MUTED,
            size_hint_y=None, height=dp(18),
        )
        self.add_widget(self.val_lbl)
        self.add_widget(self.title_lbl)

    def update(self, value, color=None):
        self.val_lbl.text = str(value)
        if color:
            self.val_lbl.color = color


class StyledInput(TextInput):
    def __init__(self, hint="", default="", numeric=False, **kwargs):
        super().__init__(
            hint_text=hint,
            text=str(default),
            multiline=False,
            font_size=sp(17),
            foreground_color=WHITE,
            background_color=(0, 0, 0, 0),
            hint_text_color=(*MUTED[:3], 0.7),
            cursor_color=FUCHSIA,
            selection_color=(*PURPLE[:3], 0.4),
            padding=[dp(18), dp(14)],
            size_hint_y=None,
            height=dp(54),
            **kwargs,
        )
        if numeric:
            self.input_filter = "int"
        paint_bg(self, SURFACE2, radius=12)


class PurpleButton(Button):
    def __init__(self, text, secondary=False, danger=False, **kwargs):
        super().__init__(
            text=text,
            font_size=sp(16),
            bold=True,
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=WHITE,
            size_hint_y=None,
            height=dp(54),
            **kwargs,
        )
        if danger:
            self._bg_color = RED
        elif secondary:
            self._bg_color = SURFACE2
        else:
            self._bg_color = PURPLE

        paint_bg(self, self._bg_color, radius=14)

        self.bind(state=self._on_state)

    def _on_state(self, instance, state):
        self.color = (*PURPLE[:3], 1) if state == "down" else WHITE


class ECGGraph(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pts = deque(maxlen=60)
        self.bind(pos=self._draw, size=self._draw)

    def push(self, bpm: int):
        self._pts.append(bpm)
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        pts = list(self._pts)
        if len(pts) < 2 or self.width < 2:
            return
        lo = min(pts) - 5
        hi = max(pts) + 5
        if hi == lo:
            hi = lo + 1
        w, h = self.width, self.height
        x0, y0 = self.pos

        coords = []
        for i, v in enumerate(pts):
            x = x0 + (i / (len(pts) - 1)) * w
            y = y0 + ((v - lo) / (hi - lo)) * h
            coords += [x, y]

        with self.canvas:
            # Faint fill polygon
            Color(*PURPLE[:3], 0.15)
            from kivy.graphics import Mesh
            fill_v = [x0, y0, 0, 0]
            for i in range(0, len(coords), 2):
                fill_v += [coords[i], coords[i+1], 0, 0]
            fill_v += [coords[-2], y0, 0, 0]
            n = len(fill_v) // 4
            Mesh(vertices=fill_v, indices=list(range(n)), mode="triangle_fan")

            # Line
            Color(*PURPLE)
            Line(points=coords, width=dp(1.5), cap="round", joint="round")

            # Live dot
            Color(*FUCHSIA)
            r = dp(4)
            Ellipse(pos=(coords[-2] - r, coords[-1] - r), size=(r*2, r*2))


# ── Onboarding ────────────────────────────────────────────────────────────────

class OnboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="onboard", **kwargs)
        self._data = {}
        self._build_step1()

    def _base_layout(self):
        """Fresh vertical layout with standard padding."""
        layout = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(60), dp(32), dp(40)],
            spacing=dp(16),
        )
        self.clear_widgets()
        self.add_widget(layout)
        return layout

    def _step_label(self, layout, step, title, sub):
        layout.add_widget(Label(
            text=f"step {step} of 3",
            font_size=sp(13), color=FUCHSIA,
            size_hint_y=None, height=dp(22),
            halign="left",
        ))
        layout.add_widget(Label(
            text=title,
            font_size=sp(28), bold=True, color=WHITE,
            size_hint_y=None, height=dp(48),
            halign="left",
        ))
        layout.add_widget(Label(
            text=sub,
            font_size=sp(14), color=MUTED,
            size_hint_y=None, height=dp(24),
            halign="left",
        ))

    # Step 1 — name
    def _build_step1(self):
        l = self._base_layout()

        # Logo / wordmark at top
        l.add_widget(Label(
            text="PaceRing",
            font_size=sp(36), bold=True, color=FUCHSIA,
            size_hint_y=None, height=dp(56),
        ))

        self._step_label(l, 1, "What's your name?", "So we can make this feel like yours.")

        self.name_input = StyledInput(hint="your name", default="")
        l.add_widget(self.name_input)

        l.add_widget(Widget())  # spacer

        btn = PurpleButton("continue →")
        btn.bind(on_press=self._from_step1)
        l.add_widget(btn)

    def _from_step1(self, *_):
        name = self.name_input.text.strip() or "friend"
        self._data["name"] = name
        self._build_step2()

    # Step 2 — resting HR slider
    def _build_step2(self):
        l = self._base_layout()
        self._step_label(l, 2, "your resting\nheart rate", "used to detect spikes accurately")

        # Big slider value display
        val_row = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(40))
        self._rest_val = Label(text="65", font_size=sp(48), bold=True, color=PURPLE)
        self._thresh_val = Label(text="115", font_size=sp(48), bold=True, color=FUCHSIA)
        val_row.add_widget(self._rest_val)
        val_row.add_widget(self._thresh_val)
        l.add_widget(val_row)

        lbl_row = BoxLayout(size_hint_y=None, height=dp(20))
        lbl_row.add_widget(Label(text="resting BPM", font_size=sp(12), color=MUTED))
        lbl_row.add_widget(Label(text="alert above", font_size=sp(12), color=MUTED))
        l.add_widget(lbl_row)

        self.rest_slider = Slider(min=40, max=100, value=65, step=1,
                                  size_hint_y=None, height=dp(50))
        self.rest_slider.bind(value=self._update_rest)
        l.add_widget(self.rest_slider)

        l.add_widget(Label(
            text="drag to set your resting BPM",
            font_size=sp(12), color=MUTED,
            size_hint_y=None, height=dp(20),
        ))

        l.add_widget(Widget())

        btn = PurpleButton("continue →")
        btn.bind(on_press=self._from_step2)
        l.add_widget(btn)

        skip = Button(
            text="use defaults",
            font_size=sp(13), color=MUTED,
            background_normal="", background_color=(0,0,0,0),
            size_hint_y=None, height=dp(36),
        )
        skip.bind(on_press=self._from_step2)
        l.add_widget(skip)

    def _update_rest(self, inst, val):
        v = int(val)
        self._rest_val.text = str(v)
        self._thresh_val.text = str(v + 50)

    def _from_step2(self, *_):
        self._data["resting_hr"] = int(self.rest_slider.value)
        self._data["threshold"]  = int(self.rest_slider.value) + 50
        self._build_step3()

    # Step 3 — spike sensitivity
    def _build_step3(self):
        l = self._base_layout()
        self._step_label(l, 3, "spike sensitivity", "how fast does your HR rise during episodes?")

        self._spike_lbl = Label(
            text="+30 BPM",
            font_size=sp(44), bold=True, color=FUCHSIA,
            size_hint_y=None, height=dp(72),
        )
        l.add_widget(self._spike_lbl)

        spike_slider = Slider(min=15, max=60, value=30, step=5,
                              size_hint_y=None, height=dp(50))
        spike_slider.bind(value=lambda i, v: setattr(self._spike_lbl, "text", f"+{int(v)} BPM"))
        l.add_widget(spike_slider)

        self._dur_lbl = Label(
            text="alert after  10 s",
            font_size=sp(16), color=WHITE,
            size_hint_y=None, height=dp(36),
        )
        l.add_widget(self._dur_lbl)

        dur_slider = Slider(min=5, max=30, value=10, step=5,
                            size_hint_y=None, height=dp(50))
        dur_slider.bind(value=lambda i, v: setattr(self._dur_lbl, "text", f"alert after  {int(v)} s"))
        l.add_widget(dur_slider)

        l.add_widget(Widget())

        btn = PurpleButton("start monitoring")
        btn.bind(on_press=lambda *_: self._finish(int(spike_slider.value), int(dur_slider.value)))
        l.add_widget(btn)

    def _finish(self, spike, dur):
        self._data["spike_delta"]    = spike
        self._data["sustained_secs"] = dur
        save_profile(self._data)
        app = App.get_running_app()
        app.launch_monitor(self._data)


# ── Settings ──────────────────────────────────────────────────────────────────

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="settings", **kwargs)
        self._build()

    def _build(self):
        root = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(56), dp(28), dp(32)],
            spacing=dp(16),
        )

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12))
        back = Button(
            text="←", font_size=sp(22),
            background_normal="", background_color=(0,0,0,0),
            color=FUCHSIA, size_hint_x=None, width=dp(44),
        )
        back.bind(on_press=lambda *_: setattr(self.manager, "current", "monitor"))
        hdr.add_widget(back)
        hdr.add_widget(Label(text="settings", font_size=sp(22), bold=True, color=WHITE, halign="left"))
        root.add_widget(hdr)

        root.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self._fields = {}
        field_defs = [
            ("name",           "your name",            False),
            ("resting_hr",     "resting HR (BPM)",     True),
            ("threshold",      "alert threshold (BPM)",True),
            ("spike_delta",    "spike delta (+BPM)",   True),
            ("sustained_secs", "sustained duration (s)",True),
        ]
        for key, label, numeric in field_defs:
            root.add_widget(Label(
                text=label, font_size=sp(12), color=MUTED,
                size_hint_y=None, height=dp(20), halign="left",
            ))
            inp = StyledInput(hint=label, numeric=numeric)
            self._fields[key] = inp
            root.add_widget(inp)

        root.add_widget(Widget())

        save_btn = PurpleButton("save changes")
        save_btn.bind(on_press=self._save)
        root.add_widget(save_btn)

        reset_btn = PurpleButton("reset profile", danger=True)
        reset_btn.bind(on_press=self._reset)
        root.add_widget(reset_btn)

        self.add_widget(root)

    def on_enter(self):
        p = load_profile() or {}
        for key, inp in self._fields.items():
            inp.text = str(p.get(key, ""))

    def _save(self, *_):
        p = load_profile() or {}
        for key, inp in self._fields.items():
            p[key] = inp.text.strip()
        save_profile(p)
        self.manager.current = "monitor"

    def _reset(self, *_):
        if os.path.exists(PROFILE_FILE):
            os.remove(PROFILE_FILE)
        App.get_running_app().stop()


# ── Monitor screen ────────────────────────────────────────────────────────────

class MonitorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="monitor", **kwargs)
        self.ble_worker = None
        self._alert_up  = False
        self._build_ui()

    def _build_ui(self):
        root = FloatLayout()

        # Main scrollable column
        col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(52), dp(24), dp(24)],
            spacing=dp(14),
            size_hint=(1, 1),
        )

        # ── Row 1: Greeting + settings ──
        top = BoxLayout(size_hint_y=None, height=dp(44))
        self.greeting_lbl = Label(
            text="", font_size=sp(14), color=MUTED,
            halign="left", valign="middle", size_hint_x=0.85,
        )
        self.greeting_lbl.bind(size=lambda w, _: setattr(w, "text_size", w.size))
        top.add_widget(self.greeting_lbl)

        gear = Button(
            text="☰", font_size=sp(18),
            background_normal="", background_color=(0,0,0,0),
            color=FUCHSIA, size_hint=(None, None), size=(dp(40), dp(40)),
        )
        gear.bind(on_press=lambda *_: setattr(self.manager, "current", "settings"))
        top.add_widget(gear)
        col.add_widget(top)

        # ── Row 2: Status pill ──
        self.status_pill = PillLabel("not connected", bg=SURFACE2, text_color=MUTED)
        status_anchor = BoxLayout(size_hint_y=None, height=dp(32))
        status_anchor.add_widget(self.status_pill)
        status_anchor.add_widget(Widget())
        col.add_widget(status_anchor)

        # ── Row 3: BPM number ──
        bpm_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(110),
        )
        self.bpm_lbl = Label(
            text="--",
            font_size=sp(82), bold=True, color=WHITE,
            size_hint_y=None, height=dp(90),
        )
        self.bpm_unit = Label(
            text="BPM",
            font_size=sp(14), color=MUTED,
            size_hint_y=None, height=dp(20),
        )
        bpm_box.add_widget(self.bpm_lbl)
        bpm_box.add_widget(self.bpm_unit)
        col.add_widget(bpm_box)

        # ── Row 4: HRV pill ──
        self.hrv_lbl = Label(
            text="HRV  —",
            font_size=sp(14), color=FUCHSIA,
            size_hint_y=None, height=dp(24),
        )
        col.add_widget(self.hrv_lbl)

        # ── Row 5: Graph ──
        graph_card = BoxLayout(size_hint_y=None, height=dp(90), padding=dp(12))
        paint_bg(graph_card, SURFACE, radius=16)
        self.graph = ECGGraph()
        graph_card.add_widget(self.graph)
        col.add_widget(graph_card)

        # ── Row 6: Stat cards ──
        stats = BoxLayout(size_hint_y=None, height=dp(78), spacing=dp(10))
        self.card_rest   = StatCard("resting", "--", "BPM")
        self.card_hrv    = StatCard("avg HRV", "--", "ms")
        self.card_status = StatCard("status", "idle")
        stats.add_widget(self.card_rest)
        stats.add_widget(self.card_hrv)
        stats.add_widget(self.card_status)
        col.add_widget(stats)

        # ── Row 7: Alert card (hidden) ──
        self.alert_card = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=0,
            padding=[dp(16), dp(0)],
            opacity=0,
        )
        paint_bg(self.alert_card, (0.22, 0.05, 0.10, 1), radius=16)
        self.alert_lbl = Label(
            text="", font_size=sp(13), color=(1, 0.55, 0.60, 1),
            halign="center", valign="middle",
        )
        self.alert_lbl.bind(size=lambda w, _: setattr(w, "text_size", (w.width - dp(24), None)))
        self.alert_card.add_widget(self.alert_lbl)
        col.add_widget(self.alert_card)

        # ── Row 8: Connect button ──
        col.add_widget(Widget())  # push button down
        self.connect_btn = PurpleButton("connect to band")
        self.connect_btn.bind(on_press=self._start)
        col.add_widget(self.connect_btn)

        root.add_widget(col)
        self.add_widget(root)

    def on_enter(self):
        p = load_profile()
        if p:
            self.greeting_lbl.text = time_greeting(p.get("name", ""))
            self.card_rest.update(str(p.get("resting_hr", "--")))
        Clock.schedule_interval(self._tick_greeting, 60)

    def _tick_greeting(self, *_):
        p = load_profile()
        if p:
            self.greeting_lbl.text = time_greeting(p.get("name", ""))

    def _start(self, *_):
        self.connect_btn.disabled = True
        self.connect_btn.text = "connecting..."
        p = load_profile() or {}
        config = AlertConfig(
            sustained_hr_threshold=int(p.get("threshold", 110)),
            sustained_duration_secs=int(p.get("sustained_secs", 10)),
            spike_bpm_delta=int(p.get("spike_delta", 30)),
            spike_window_secs=30,
        )
        self.ble_worker = BLEWorker(
            on_bpm=self._on_bpm,
            on_status=self._on_status,
            on_alert=self._on_alert,
            scenario="pots_spike",
        )
        self.ble_worker.alert_engine = AlertEngine(config)
        self.ble_worker.start()

    def _on_status(self, txt: str):
        self.status_pill.set_text(txt)
        connected = any(x in txt.lower() for x in ["connected", "simulator", "monitoring"])
        self.status_pill.lbl.color = GREEN if connected else MUTED
        if connected:
            self.card_status.update("live", GREEN)

    def _on_bpm(self, bpm: int, rmssd: Optional[float]):
        self.bpm_lbl.text = str(bpm)
        self.graph.push(bpm)

        # Colour
        if bpm < 90:
            c = WHITE
        elif bpm < 110:
            c = AMBER
        else:
            c = RED
        self.bpm_lbl.color = c

        # Subtle pulse
        anim = Animation(font_size=sp(86), duration=0.08) + Animation(font_size=sp(82), duration=0.18)
        anim.start(self.bpm_lbl)

        if rmssd:
            self.hrv_lbl.text = f"HRV  {rmssd:.0f} ms"
            self.card_hrv.update(f"{rmssd:.0f}", FUCHSIA)

        # Auto-dismiss alert on recovery
        if bpm < 95 and self._alert_up:
            self._dismiss_alert()

    def _on_alert(self, alert: AlertEvent):
        self._alert_up = True
        self.alert_lbl.text = f"⚠  {alert.message}"
        self.alert_card.opacity = 1
        Animation(height=dp(88), duration=0.3).start(self.alert_card)
        self.card_status.update("ALERT", RED)

        try:
            from plyer import vibrator
            vibrator.vibrate(time=1.5)
        except Exception:
            pass

    def _dismiss_alert(self, *_):
        self._alert_up = False
        self.card_status.update("live", GREEN)
        anim = Animation(height=0, opacity=0, duration=0.22)
        anim.start(self.alert_card)


# ── App ───────────────────────────────────────────────────────────────────────

class PaceRingApp(App):
    def build(self):
        Window.clearcolor = BG
        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))
        p = load_profile()
        if p:
            self._add_monitor_screens(p)
            self.sm.current = "monitor"
        else:
            self.sm.add_widget(OnboardScreen())
            self.sm.current = "onboard"
        return self.sm

    def launch_monitor(self, profile):
        self._add_monitor_screens(profile)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "monitor"

    def _add_monitor_screens(self, profile):
        if not self.sm.has_screen("monitor"):
            self.sm.add_widget(MonitorScreen())
        if not self.sm.has_screen("settings"):
            self.sm.add_widget(SettingsScreen())


if __name__ == "__main__":
    PaceRingApp().run()
ENDOFFILE
echo "Done"
