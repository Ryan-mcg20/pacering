import asyncio
import threading
import csv
import json
import os
from datetime import datetime
from collections import deque
from time import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.animation import Animation

USE_SIMULATOR = True

if USE_SIMULATOR:
    from fake_ble import FakeBLEWorker as BLEWorker
else:
    try:
        from bleak import BleakScanner, BleakClient
    except ImportError:
        pass
    BLEWorker = None

from alert_engine import AlertEngine, AlertConfig, AlertEvent

HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
PROFILE_FILE = "pacering_profile.json"
LOG_FILE = f"hr_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# ── Colours ───────────────────────────────────────────────────────────────────
BG        = (0.063, 0.051, 0.102, 1)   # #100d1a
PURPLE    = (0.486, 0.114, 0.584, 1)   # #7c1d95
PURPLE2   = (0.424, 0.169, 0.855, 1)   # #6c2bda
LAVENDER  = (0.929, 0.914, 0.996, 1)   # #ede9fe
LILAC     = (0.655, 0.561, 0.753, 1)   # #a78bfa
MUTED     = (0.427, 0.373, 0.627, 1)   # #6d5fa0
FUCHSIA   = (0.910, 0.475, 0.976, 1)   # #e879f9
DARK1     = (0.051, 0.043, 0.086, 1)   # #0d0b16
DARK2     = (0.118, 0.086, 0.188, 1)   # #1e1630
BORDER    = (0.231, 0.184, 0.369, 1)   # #3b2f5e
GREEN     = (0.302, 0.890, 0.400, 1)
RED       = (0.957, 0.243, 0.325, 1)

def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE) as f:
            return json.load(f)
    return None

def save_profile(data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f)

def init_log():
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "bpm", "rmssd_ms", "alert_type"])

def append_log(bpm, rmssd, alert_type=""):
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(), bpm,
            f"{rmssd:.1f}" if rmssd else "", alert_type,
        ])

def get_greeting(name):
    h = datetime.now().hour
    if 6 <= h < 12:   return f"good morning, {name}"
    if 12 <= h < 17:  return f"good afternoon, {name}"
    if 17 <= h < 21:  return f"good evening, {name}"
    return f"hey {name}, rest up"

# ── Helpers ───────────────────────────────────────────────────────────────────

def make_bg(widget, color, radius=16):
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda w, v: setattr(rect, 'pos', v),
                size=lambda w, v: setattr(rect, 'size', v))
    return rect

def purple_btn(text, height=52, font=16):
    btn = Button(
        text=text, font_size=f"{font}sp",
        size_hint_y=None, height=height,
        background_color=(0, 0, 0, 0),
        color=LAVENDER,
    )
    make_bg(btn, PURPLE2, radius=14)
    return btn

def ghost_btn(text, height=40, font=12):
    btn = Button(
        text=text, font_size=f"{font}sp",
        size_hint_y=None, height=height,
        background_color=(0, 0, 0, 0),
        color=MUTED,
    )
    return btn

# ── Real BLE Worker ───────────────────────────────────────────────────────────

class RealBLEWorker:
    def __init__(self, on_bpm, on_status, on_alert, config):
        self.on_bpm = on_bpm
        self.on_status = on_status
        self.on_alert = on_alert
        self.alert_engine = AlertEngine(config)
        self._loop = None
        self._running = False

    def start(self):
        threading.Thread(target=self._run_loop, daemon=True).start()

    def stop(self):
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._ble_main())

    def _parse_hr(self, data):
        flags = data[0]
        hr_16 = flags & 0x01
        rr_present = (flags >> 4) & 0x01
        bpm = int.from_bytes(data[1:3], "little") if hr_16 else data[1]
        rr_start = 3 if hr_16 else 2
        rr = []
        if rr_present:
            for i in range(rr_start, len(data) - 1, 2):
                rr.append(int.from_bytes(data[i:i+2], "little") / 1024.0)
        return bpm, rr

    def _handler(self, sender, data):
        bpm, rr = self._parse_hr(data)
        alert = self.alert_engine.update(bpm, rr)
        rmssd = self.alert_engine.calculate_rmssd()
        Clock.schedule_once(lambda dt: self.on_bpm(bpm, rmssd), 0)
        if alert:
            Clock.schedule_once(lambda dt: self.on_alert(alert), 0)
        append_log(bpm, rmssd, alert.type if alert else "")

    async def _ble_main(self):
        self._running = True
        Clock.schedule_once(lambda dt: self.on_status("scanning for band..."), 0)
        devices = await BleakScanner.discover(timeout=30.0)
        found_names = [d.name for d in devices if d.name]
        Clock.schedule_once(lambda dt: self.on_status(f"found: {found_names[:3]}"), 0)
        keywords = ["mi band", "xiaomi", "band 10", "smart band", "miband", "mbs10"]
        address = None
        for d in devices:
            if d.name and any(k in d.name.lower() for k in keywords):
                address = d.address
                Clock.schedule_once(lambda dt: self.on_status(f"found: {d.name}"), 0)
                break
        if not address:
            Clock.schedule_once(lambda dt: self.on_status("band not found — close Mi Fitness and retry"), 0)
            return
        Clock.schedule_once(lambda dt: self.on_status("connecting..."), 0)
        try:
            async with BleakClient(address, timeout=20.0) as client:
                Clock.schedule_once(lambda dt: self.on_status("connected — monitoring"), 0)
                await client.start_notify(HR_MEASUREMENT_UUID, self._handler)
                while self._running and client.is_connected:
                    await asyncio.sleep(0.5)
                await client.stop_notify(HR_MEASUREMENT_UUID)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.on_status(f"error: {e}"), 0)

# ── Onboarding Screens ────────────────────────────────────────────────────────

class OnboardScreen(Screen):
    def __init__(self, step, total, title, subtitle, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=[28, 48, 28, 28], spacing=16)
        with self.canvas.before:
            Color(*BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(self._bg, 'pos', v),
                  size=lambda w, v: setattr(self._bg, 'size', v))

        # Step badge
        badge = Label(
            text=f"step {step} of {total}",
            font_size="11sp", color=LILAC,
            size_hint_y=None, height=24,
        )
        root.add_widget(badge)

        # Title
        root.add_widget(Label(
            text=title, font_size="22sp",
            color=LAVENDER, halign="center",
            size_hint_y=None, height=60,
            text_size=(Window.width - 56, None),
        ))

        # Subtitle
        root.add_widget(Label(
            text=subtitle, font_size="13sp",
            color=MUTED, halign="center",
            size_hint_y=None, height=36,
            text_size=(Window.width - 56, None),
        ))

        self.content_area = BoxLayout(
            orientation="vertical", spacing=12,
            size_hint_y=None, height=180,
        )
        root.add_widget(self.content_area)
        root.add_widget(BoxLayout())  # spacer

        # Dots
        dots_box = BoxLayout(size_hint_y=None, height=20,
                             spacing=6, size_hint_x=None, width=total*22)
        dots_box.pos_hint = {"center_x": 0.5}
        self.dots = []
        for i in range(total):
            d = Label(
                text="●" if i == step - 1 else "○",
                font_size="12sp",
                color=LILAC if i == step - 1 else MUTED,
            )
            self.dots.append(d)
            dots_box.add_widget(d)
        root.add_widget(dots_box)

        self.add_widget(root)
        self.root_layout = root


class Step1Screen(OnboardScreen):
    def __init__(self, on_done, **kwargs):
        super().__init__(1, 3, "what's your name?",
                         "so we can make this feel like yours",
                         name="step1", **kwargs)
        self.on_done = on_done

        self.name_input = TextInput(
            hint_text="your name",
            font_size="18sp",
            size_hint_y=None, height=52,
            background_color=DARK1,
            foreground_color=LAVENDER,
            cursor_color=LILAC,
            hint_text_color=MUTED,
            padding=[16, 14, 16, 14],
            multiline=False,
        )
        self.content_area.add_widget(self.name_input)

        btn = purple_btn("continue →")
        btn.bind(on_press=self.next)
        self.content_area.add_widget(btn)

    def next(self, *a):
        name = self.name_input.text.strip()
        if not name:
            name = "friend"
        self.on_done(name)


class Step2Screen(OnboardScreen):
    def __init__(self, on_done, **kwargs):
        super().__init__(2, 3, "your resting heart rate",
                         "used to detect spikes accurately",
                         name="step2", **kwargs)
        self.on_done = on_done
        self.resting = 65
        self.threshold = 110

        row = BoxLayout(spacing=12, size_hint_y=None, height=80)

        rest_box = BoxLayout(orientation="vertical", spacing=4)
        self.rest_lbl = Label(text="65", font_size="28sp",
                              color=LILAC, bold=True)
        rest_box.add_widget(self.rest_lbl)
        rest_box.add_widget(Label(text="resting BPM", font_size="11sp",
                                  color=MUTED))
        row.add_widget(rest_box)

        thresh_box = BoxLayout(orientation="vertical", spacing=4)
        self.thresh_lbl = Label(text="110", font_size="28sp",
                                color=LILAC, bold=True)
        thresh_box.add_widget(self.thresh_lbl)
        thresh_box.add_widget(Label(text="alert above", font_size="11sp",
                                    color=MUTED))
        row.add_widget(thresh_box)
        self.content_area.add_widget(row)

        self.rest_slider = Slider(min=40, max=100, value=65, step=1,
                                  size_hint_y=None, height=36)
        self.rest_slider.bind(value=self.on_rest)
        self.content_area.add_widget(self.rest_slider)

        btn = purple_btn("continue →")
        btn.bind(on_press=self.next)
        self.content_area.add_widget(btn)

        ghost = ghost_btn("use defaults")
        ghost.bind(on_press=self.next)
        self.content_area.add_widget(ghost)

    def on_rest(self, slider, val):
        self.resting = int(val)
        self.rest_lbl.text = str(self.resting)
        self.threshold = self.resting + 45
        self.thresh_lbl.text = str(self.threshold)

    def next(self, *a):
        self.on_done(self.resting, self.threshold)


class Step3Screen(OnboardScreen):
    def __init__(self, on_done, **kwargs):
        super().__init__(3, 3, "spike sensitivity",
                         "alert me when HR rises by...",
                         name="step3", **kwargs)
        self.on_done = on_done
        self.spike = 30
        self.sustained = 10

        row = BoxLayout(spacing=12, size_hint_y=None, height=80)

        spike_box = BoxLayout(orientation="vertical", spacing=4)
        self.spike_lbl = Label(text="+30", font_size="28sp",
                               color=LILAC, bold=True)
        spike_box.add_widget(self.spike_lbl)
        spike_box.add_widget(Label(text="BPM spike", font_size="11sp",
                                   color=MUTED))
        row.add_widget(spike_box)

        sus_box = BoxLayout(orientation="vertical", spacing=4)
        self.sus_lbl = Label(text="10s", font_size="28sp",
                             color=LILAC, bold=True)
        sus_box.add_widget(self.sus_lbl)
        sus_box.add_widget(Label(text="sustained", font_size="11sp",
                                 color=MUTED))
        row.add_widget(sus_box)
        self.content_area.add_widget(row)

        self.spike_slider = Slider(min=15, max=50, value=30, step=1,
                                   size_hint_y=None, height=36)
        self.spike_slider.bind(value=self.on_spike)
        self.content_area.add_widget(self.spike_slider)

        btn = purple_btn("let's go →")
        btn.bind(on_press=self.next)
        self.content_area.add_widget(btn)

    def on_spike(self, slider, val):
        self.spike = int(val)
        self.spike_lbl.text = f"+{self.spike}"

    def next(self, *a):
        self.on_done(self.spike, self.sustained)


# ── Main Monitor Screen ───────────────────────────────────────────────────────

class MonitorScreen(Screen):
    def __init__(self, profile, **kwargs):
        super().__init__(name="monitor", **kwargs)
        self.profile = profile
        self.bpm_history = deque(maxlen=60)
        self.ble_worker = None
        self.alert_showing = False

        with self.canvas.before:
            Color(*BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(self._bg, 'pos', v),
                  size=lambda w, v: setattr(self._bg, 'size', v))

        root = BoxLayout(orientation="vertical",
                         padding=[24, 36, 24, 20], spacing=10)

        # Top row — greeting + profile button
        top = BoxLayout(size_hint_y=None, height=36)
        self.greeting_lbl = Label(
            text=get_greeting(profile["name"]),
            font_size="14sp", color=LILAC,
            halign="left", valign="middle",
        )
        self.greeting_lbl.bind(size=self.greeting_lbl.setter("text_size"))
        top.add_widget(self.greeting_lbl)

        self.profile_btn = Button(
            text=profile["name"][0].upper(),
            font_size="13sp",
            size_hint=(None, None), size=(32, 32),
            background_color=(0, 0, 0, 0),
            color=LILAC,
        )
        make_bg(self.profile_btn, DARK2, radius=16)
        self.profile_btn.bind(on_press=self.open_settings)
        top.add_widget(self.profile_btn)
        root.add_widget(top)

        # Status row
        self.status_lbl = Label(
            text="not connected",
            font_size="11sp", color=MUTED,
            size_hint_y=None, height=20,
        )
        root.add_widget(self.status_lbl)

        # BPM number
        self.bpm_lbl = Label(
            text="--",
            font_size="96sp", bold=True,
            color=LAVENDER,
            size_hint_y=None, height=110,
        )
        root.add_widget(self.bpm_lbl)

        root.add_widget(Label(
            text="BPM", font_size="11sp", color=MUTED,
            letter_spacing=3,
            size_hint_y=None, height=18,
        ))

        # HRV pill
        self.hrv_lbl = Label(
            text="HRV  --  ms",
            font_size="12sp", color=LILAC,
            size_hint_y=None, height=32,
        )
        root.add_widget(self.hrv_lbl)

        # Graph
        graph_outer = BoxLayout(
            size_hint_y=None, height=70,
            padding=[0, 0, 0, 0],
        )
        make_bg(graph_outer, DARK1, radius=12)
        self.graph_widget = GraphWidget(size_hint=(1, 1))
        graph_outer.add_widget(self.graph_widget)
        root.add_widget(graph_outer)

        # Stat row
        stat_row = BoxLayout(size_hint_y=None, height=64, spacing=8)
        self.stat_resting = self._stat(str(profile.get("resting", 65)), "resting")
        self.stat_hrv = self._stat("--", "HRV ms")
        self.stat_status = self._stat("--", "status")
        stat_row.add_widget(self.stat_resting[0])
        stat_row.add_widget(self.stat_hrv[0])
        stat_row.add_widget(self.stat_status[0])
        root.add_widget(stat_row)

        # Alert slot
        self.alert_slot = BoxLayout(size_hint_y=None, height=0)
        root.add_widget(self.alert_slot)

        # Connect button
        self.connect_btn = purple_btn("connect to band", height=52)
        self.connect_btn.bind(on_press=self.start_monitoring)
        root.add_widget(self.connect_btn)

        # Log label
        root.add_widget(Label(
            text=f"logging to {LOG_FILE}",
            font_size="10sp", color=(0.2, 0.17, 0.32, 1),
            size_hint_y=None, height=18,
        ))

        self.add_widget(root)
        init_log()

    def _stat(self, val, lbl):
        box = BoxLayout(orientation="vertical", spacing=2)
        make_bg(box, DARK1, radius=10)
        v = Label(text=val, font_size="14sp", color=LILAC, bold=True)
        l = Label(text=lbl, font_size="9sp", color=MUTED)
        box.add_widget(v)
        box.add_widget(l)
        return box, v, l

    def _request_ble_permissions(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.BLUETOOTH_SCAN,
                Permission.BLUETOOTH_CONNECT,
                Permission.ACCESS_FINE_LOCATION,
            ], lambda p, r: None)
        except ImportError:
            pass

    def on_enter(self):
        self._request_ble_permissions()

    def start_monitoring(self, *a):
        self.connect_btn.disabled = True
        self.connect_btn.text = "connecting..."
        config = AlertConfig(
            sustained_hr_threshold=self.profile.get("threshold", 110),
            spike_bpm_delta=self.profile.get("spike", 30),
        )
        if USE_SIMULATOR:
            from fake_ble import FakeBLEWorker
            self.ble_worker = FakeBLEWorker(
                on_bpm=self.update_bpm,
                on_status=self.update_status,
                on_alert=self.trigger_alert,
                scenario="pots_spike",
            )
        else:
            self.ble_worker = RealBLEWorker(
                on_bpm=self.update_bpm,
                on_status=self.update_status,
                on_alert=self.trigger_alert,
                config=config,
            )
        self.ble_worker.start()

    def update_status(self, status):
        self.status_lbl.text = status

    def update_bpm(self, bpm, rmssd):
        self.bpm_lbl.text = str(bpm)
        if bpm < 90:
            target = LAVENDER
        elif bpm < 110:
            target = FUCHSIA
        else:
            target = (1, 0.2, 0.3, 1)
        anim = Animation(color=target, duration=0.4)
        anim.start(self.bpm_lbl)

        if rmssd:
            self.hrv_lbl.text = f"HRV  {rmssd:.0f}  ms"
            self.stat_hrv[1].text = f"{rmssd:.0f}"

        self.bpm_history.append(bpm)
        self.graph_widget.update(list(self.bpm_history))

        if bpm < 100 and not self.alert_showing:
            self.stat_status[1].text = "all clear"
            self.stat_status[1].color = GREEN

    def trigger_alert(self, alert):
        if self.alert_showing:
            return
        self.alert_showing = True
        self.stat_status[1].text = "alert"
        self.stat_status[1].color = (1, 0.2, 0.3, 1)

        card = BoxLayout(
            orientation="vertical",
            padding=[14, 12, 14, 12],
            spacing=8,
            size_hint_y=None, height=0,
        )
        make_bg(card, (0.102, 0.051, 0.180, 1), radius=14)

        with card.canvas.before:
            Color(*BORDER)
            Line(rounded_rectangle=(card.x, card.y, card.width, card.height, 14), width=1)

        card.add_widget(Label(
            text="spike detected" if alert.type == "spike" else "sustained HR",
            font_size="13sp", color=LILAC, bold=True,
            size_hint_y=None, height=22, halign="left",
        ))
        card.add_widget(Label(
            text=alert.message,
            font_size="11sp", color=MUTED,
            text_size=(Window.width - 90, None),
            halign="left",
            size_hint_y=None, height=36,
        ))
        dismiss = purple_btn("ok — resting now", height=38, font=12)
        dismiss.bind(on_press=lambda *a: self.dismiss_alert(card))
        card.add_widget(dismiss)

        self.alert_slot.add_widget(card)
        anim = Animation(height=110, duration=0.35)
        anim.start(card)
        anim2 = Animation(height=110, duration=0.35)
        anim2.start(self.alert_slot)

        try:
            from plyer import vibrator
            vibrator.vibrate(time=1.5)
        except Exception:
            pass

    def dismiss_alert(self, card):
        anim = Animation(height=0, duration=0.25)
        anim.bind(on_complete=lambda *a: self.alert_slot.remove_widget(card))
        anim.start(card)
        anim2 = Animation(height=0, duration=0.25)
        anim2.start(self.alert_slot)
        self.alert_showing = False
        self.stat_status[1].text = "recovering"
        self.stat_status[1].color = FUCHSIA

    def open_settings(self, *a):
        self.manager.current = "settings"


# ── Graph Widget ──────────────────────────────────────────────────────────────

class GraphWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._points = []
        self.bind(size=self._redraw, pos=self._redraw)

    def update(self, history):
        self._points = history
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        pts = self._points
        if len(pts) < 2:
            return
        w, h = self.width, self.height
        if w == 0 or h == 0:
            return
        mn = min(pts) - 5
        mx = max(pts) + 5
        rng = mx - mn or 1
        coords = []
        for i, v in enumerate(pts):
            x = self.x + (i / (len(pts) - 1)) * w
            y = self.y + ((v - mn) / rng) * (h - 8) + 4
            coords.extend([x, y])
        with self.canvas:
            Color(0.486, 0.227, 0.855, 1)
            Line(points=coords, width=1.5)


# ── Settings Screen ───────────────────────────────────────────────────────────

class SettingsScreen(Screen):
    def __init__(self, profile, on_save, **kwargs):
        super().__init__(name="settings", **kwargs)
        self.profile = profile
        self.on_save = on_save

        with self.canvas.before:
            Color(*BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(self._bg, 'pos', v),
                  size=lambda w, v: setattr(self._bg, 'size', v))

        root = BoxLayout(orientation="vertical",
                         padding=[24, 48, 24, 24], spacing=14)

        back = ghost_btn("← back", height=32)
        back.bind(on_press=lambda *a: setattr(self.manager, 'current', 'monitor'))
        root.add_widget(back)

        root.add_widget(Label(
            text="profile", font_size="18sp", color=LAVENDER,
            bold=True, size_hint_y=None, height=36,
            halign="left",
        ))

        items = [
            ("name", profile.get("name", "")),
            ("resting BPM", str(profile.get("resting", 65))),
            ("alert threshold", f"{profile.get('threshold', 110)} BPM"),
            ("spike delta", f"+{profile.get('spike', 30)} BPM"),
            ("vibration", "on"),
            ("sound alerts", "on"),
        ]
        for lbl, val in items:
            row = BoxLayout(size_hint_y=None, height=48, padding=[14, 0])
            make_bg(row, DARK1, radius=10)
            row.add_widget(Label(text=lbl, font_size="13sp",
                                 color=LAVENDER, halign="left"))
            row.add_widget(Label(text=val, font_size="13sp",
                                 color=LILAC, halign="right"))
            root.add_widget(row)

        root.add_widget(BoxLayout())

        save = purple_btn("save & back")
        save.bind(on_press=lambda *a: setattr(self.manager, 'current', 'monitor'))
        root.add_widget(save)

        self.add_widget(root)


# ── App ───────────────────────────────────────────────────────────────────────

class PaceRingApp(App):
    def build(self):
        Window.clearcolor = BG
        self.sm = ScreenManager(transition=SlideTransition())
        profile = load_profile()
        if profile:
            self._launch_monitor(profile)
        else:
            self._launch_onboarding()
        return self.sm

    def _launch_onboarding(self):
        self._profile_temp = {}
        s1 = Step1Screen(on_done=self._ob1_done)
        s2 = Step2Screen(on_done=self._ob2_done)
        s3 = Step3Screen(on_done=self._ob3_done)
        self.sm.add_widget(s1)
        self.sm.add_widget(s2)
        self.sm.add_widget(s3)
        self.sm.current = "step1"

    def _ob1_done(self, name):
        self._profile_temp["name"] = name
        self.sm.current = "step2"

    def _ob2_done(self, resting, threshold):
        self._profile_temp["resting"] = resting
        self._profile_temp["threshold"] = threshold
        self.sm.current = "step3"

    def _ob3_done(self, spike, sustained):
        self._profile_temp["spike"] = spike
        self._profile_temp["sustained"] = sustained
        save_profile(self._profile_temp)
        self._launch_monitor(self._profile_temp)

    def _launch_monitor(self, profile):
        monitor = MonitorScreen(profile=profile)
        settings = SettingsScreen(
            profile=profile,
            on_save=lambda: None,
        )
        self.sm.add_widget(monitor)
        self.sm.add_widget(settings)
        self.sm.current = "monitor"


if __name__ == "__main__":
    PaceRingApp().run()
