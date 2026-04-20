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
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation

USE_SIMULATOR = True
DEV_CODE = "Ryan_5610"

if USE_SIMULATOR:
    from fake_ble import FakeBLEWorker
else:
    try:
        from bleak import BleakScanner, BleakClient
    except ImportError:
        pass

from alert_engine import AlertEngine, AlertConfig, AlertEvent

HR_SERVICE_UUID     = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
PROFILE_FILE        = "pacering_profile.json"
LOG_FILE            = f"hr_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

BG       = (0.063, 0.051, 0.102, 1)
PURPLE2  = (0.424, 0.169, 0.855, 1)
LAVENDER = (0.929, 0.914, 0.996, 1)
LILAC    = (0.655, 0.561, 0.753, 1)
MUTED    = (0.427, 0.373, 0.627, 1)
FUCHSIA  = (0.910, 0.475, 0.976, 1)
DARK1    = (0.051, 0.043, 0.086, 1)
DARK2    = (0.118, 0.086, 0.188, 1)
GREEN    = (0.302, 0.890, 0.400, 1)
RED      = (0.957, 0.243, 0.325, 1)


def load_profile():
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return None


def save_profile(data):
    try:
        with open(PROFILE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def init_log():
    try:
        with open(LOG_FILE, "w", newline="") as f:
            csv.writer(f).writerow(["timestamp", "bpm", "rmssd_ms", "alert_type"])
    except Exception:
        pass


def append_log(bpm, rmssd, alert_type=""):
    try:
        with open(LOG_FILE, "a", newline="") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(), bpm,
                f"{rmssd:.1f}" if rmssd else "", alert_type,
            ])
    except Exception:
        pass


def get_greeting(name):
    h = datetime.now().hour
    if 6 <= h < 12:  return f"good morning, {name}"
    if 12 <= h < 17: return f"good afternoon, {name}"
    if 17 <= h < 21: return f"good evening, {name}"
    return f"hey {name}, rest up"


def make_bg(widget, color, radius=16):
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(
        pos=lambda w, v: setattr(rect, 'pos', v),
        size=lambda w, v: setattr(rect, 'size', v),
    )
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


def ghost_btn(text, height=40, font=13):
    return Button(
        text=text, font_size=f"{font}sp",
        size_hint_y=None, height=height,
        background_color=(0, 0, 0, 0),
        color=MUTED,
    )


# ── Real BLE Worker ───────────────────────────────────────────────────────────

class RealBLEWorker:
    def __init__(self, on_bpm, on_status, on_alert, config):
        self.on_bpm    = on_bpm
        self.on_status = on_status
        self.on_alert  = on_alert
        self.alert_engine = AlertEngine(config)
        self._loop     = None
        self._running  = False

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
        flags    = data[0]
        hr_16    = flags & 0x01
        rr_pres  = (flags >> 4) & 0x01
        bpm      = int.from_bytes(data[1:3], "little") if hr_16 else data[1]
        rr_start = 3 if hr_16 else 2
        rr = []
        if rr_pres:
            for i in range(rr_start, len(data) - 1, 2):
                rr.append(int.from_bytes(data[i:i+2], "little") / 1024.0)
        return bpm, rr

    def _handler(self, sender, data):
        bpm, rr = self._parse_hr(data)
        alert   = self.alert_engine.update(bpm, rr)
        rmssd   = self.alert_engine.calculate_rmssd()
        Clock.schedule_once(lambda dt: self.on_bpm(bpm, rmssd), 0)
        if alert:
            Clock.schedule_once(lambda dt: self.on_alert(alert), 0)
        append_log(bpm, rmssd, alert.type if alert else "")

    async def _ble_main(self):
        self._running = True
        Clock.schedule_once(lambda dt: self.on_status("scanning for band..."), 0)
        devices  = await BleakScanner.discover(timeout=30.0)
        keywords = ["mi band", "xiaomi", "band 10", "smart band", "miband", "mbs10"]
        address  = None
        for d in devices:
            if d.name and any(k in d.name.lower() for k in keywords):
                address = d.address
                Clock.schedule_once(lambda dt: self.on_status(f"found: {d.name}"), 0)
                break
        if not address:
            Clock.schedule_once(
                lambda dt: self.on_status("band not found — close Mi Fitness and retry"), 0)
            return
        Clock.schedule_once(lambda dt: self.on_status("connecting..."), 0)
        try:
            async with BleakClient(address, timeout=20.0) as client:
                Clock.schedule_once(
                    lambda dt: self.on_status("connected — monitoring"), 0)
                await client.start_notify(HR_MEASUREMENT_UUID, self._handler)
                while self._running and client.is_connected:
                    await asyncio.sleep(0.5)
                await client.stop_notify(HR_MEASUREMENT_UUID)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.on_status(f"error: {e}"), 0)


# ── Onboarding ────────────────────────────────────────────────────────────────

class Step1Screen(Screen):
    def __init__(self, on_done, **kwargs):
        super().__init__(name="step1", **kwargs)
        self.on_done = on_done
        with self.canvas.before:
            Color(*BG)
            r = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(r, 'pos', v),
                  size=lambda w, v: setattr(r, 'size', v))

        root = BoxLayout(orientation="vertical",
                         padding=[36, 0, 36, 40], spacing=0)

        root.add_widget(BoxLayout(size_hint_y=0.12))

        root.add_widget(Label(text="step 1 of 3", font_size="12sp",
                              color=LILAC, size_hint_y=None, height=28,
                              halign="center"))

        root.add_widget(BoxLayout(size_hint_y=None, height=8))

        root.add_widget(Label(text="what's your name?", font_size="28sp",
                              color=LAVENDER, bold=True,
                              size_hint_y=None, height=64, halign="center"))

        root.add_widget(Label(text="so we can make this feel like yours",
                              font_size="14sp", color=MUTED,
                              size_hint_y=None, height=28, halign="center"))

        root.add_widget(BoxLayout(size_hint_y=None, height=32))

        self.name_input = TextInput(
            hint_text="your name", font_size="18sp",
            size_hint_y=None, height=56,
            background_color=DARK1, foreground_color=LAVENDER,
            cursor_color=LILAC, hint_text_color=MUTED,
            padding=[16, 16, 16, 16], multiline=False,
        )
        root.add_widget(self.name_input)

        root.add_widget(BoxLayout(size_hint_y=None, height=16))

        btn = purple_btn("continue", height=56)
        btn.bind(on_press=self._next)
        root.add_widget(btn)

        root.add_widget(BoxLayout())

        dots = BoxLayout(size_hint_y=None, height=24, spacing=6)
        dots.add_widget(Label(text="●", font_size="14sp", color=LILAC))
        dots.add_widget(Label(text="○", font_size="14sp", color=MUTED))
        dots.add_widget(Label(text="○", font_size="14sp", color=MUTED))
        root.add_widget(dots)

        self.add_widget(root)

    def _next(self, *a):
        self.on_done(self.name_input.text.strip() or "friend")


class Step2Screen(Screen):
    def __init__(self, on_done, **kwargs):
        super().__init__(name="step2", **kwargs)
        self.on_done   = on_done
        self.resting   = 65
        self.threshold = 110
        with self.canvas.before:
            Color(*BG)
            r = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(r, 'pos', v),
                  size=lambda w, v: setattr(r, 'size', v))

        root = BoxLayout(orientation="vertical",
                         padding=[36, 0, 36, 40], spacing=0)

        root.add_widget(BoxLayout(size_hint_y=0.10))

        root.add_widget(Label(text="step 2 of 3", font_size="12sp",
                              color=LILAC, size_hint_y=None, height=28,
                              halign="center"))

        root.add_widget(BoxLayout(size_hint_y=None, height=8))

        root.add_widget(Label(text="your resting heart rate",
                              font_size="28sp", color=LAVENDER, bold=True,
                              size_hint_y=None, height=64, halign="center"))

        root.add_widget(Label(text="used to detect spikes accurately",
                              font_size="14sp", color=MUTED,
                              size_hint_y=None, height=28, halign="center"))

        root.add_widget(BoxLayout(size_hint_y=None, height=24))

        vals = BoxLayout(size_hint_y=None, height=100, spacing=16)

        left = BoxLayout(orientation="vertical", spacing=4, padding=[8, 8])
        make_bg(left, DARK1, radius=12)
        self.rest_lbl = Label(text="65", font_size="36sp",
                              color=LILAC, bold=True)
        left.add_widget(self.rest_lbl)
        left.add_widget(Label(text="resting BPM", font_size="11sp",
                              color=MUTED))
        vals.add_widget(left)

        right = BoxLayout(orientation="vertical", spacing=4, padding=[8, 8])
        make_bg(right, DARK1, radius=12)
        self.thresh_lbl = Label(text="110", font_size="36sp",
                                color=LILAC, bold=True)
        right.add_widget(self.thresh_lbl)
        right.add_widget(Label(text="alert above", font_size="11sp",
                               color=MUTED))
        vals.add_widget(right)
        root.add_widget(vals)

        root.add_widget(BoxLayout(size_hint_y=None, height=16))

        self.slider = Slider(min=40, max=100, value=65, step=1,
                             size_hint_y=None, height=44)
        self.slider.bind(value=self._on_slide)
        root.add_widget(self.slider)

        root.add_widget(Label(text="drag to set your resting BPM",
                              font_size="12sp", color=MUTED,
                              size_hint_y=None, height=24, halign="center"))

        root.add_widget(BoxLayout(size_hint_y=None, height=16))

        btn = purple_btn("continue", height=56)
        btn.bind(on_press=self._next)
        root.add_widget(btn)

        skip = ghost_btn("use defaults")
        skip.bind(on_press=self._next)
        root.add_widget(skip)

        root.add_widget(BoxLayout())

        dots = BoxLayout(size_hint_y=None, height=24, spacing=6)
        dots.add_widget(Label(text="○", font_size="14sp", color=MUTED))
        dots.add_widget(Label(text="●", font_size="14sp", color=LILAC))
        dots.add_widget(Label(text="○", font_size="14sp", color=MUTED))
        root.add_widget(dots)

        self.add_widget(root)

    def _on_slide(self, s, v):
        self.resting   = int(v)
        self.threshold = self.resting + 45
        self.rest_lbl.text   = str(self.resting)
        self.thresh_lbl.text = str(self.threshold)

    def _next(self, *a):
        self.on_done(self.resting, self.threshold)


class Step3Screen(Screen):
    def __init__(self, on_done, **kwargs):
        super().__init__(name="step3", **kwargs)
        self.on_done = on_done
        self.spike   = 30
        with self.canvas.before:
            Color(*BG)
            r = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(r, 'pos', v),
                  size=lambda w, v: setattr(r, 'size', v))

        root = BoxLayout(orientation="vertical",
                         padding=[36, 0, 36, 40], spacing=0)

        root.add_widget(BoxLayout(size_hint_y=0.10))

        root.add_widget(Label(text="step 3 of 3", font_size="12sp",
                              color=LILAC, size_hint_y=None, height=28,
                              halign="center"))

        root.add_widget(BoxLayout(size_hint_y=None, height=8))

        root.add_widget(Label(text="spike sensitivity", font_size="28sp",
                              color=LAVENDER, bold=True,
                              size_hint_y=None, height=64, halign="center"))

        root.add_widget(Label(text="alert me when HR rises by...",
                              font_size="14sp", color=MUTED,
                              size_hint_y=None, height=28, halign="center"))

        root.add_widget(BoxLayout(size_hint_y=None, height=24))

        vals = BoxLayout(size_hint_y=None, height=100, spacing=16)

        left = BoxLayout(orientation="vertical", spacing=4, padding=[8, 8])
        make_bg(left, DARK1, radius=12)
        self.spike_lbl = Label(text="+30", font_size="36sp",
                               color=LILAC, bold=True)
        left.add_widget(self.spike_lbl)
        left.add_widget(Label(text="BPM spike", font_size="11sp", color=MUTED))
        vals.add_widget(left)

        right = BoxLayout(orientation="vertical", spacing=4, padding=[8, 8])
        make_bg(right, DARK1, radius=12)
        right.add_widget(Label(text="10s", font_size="36sp",
                               color=LILAC, bold=True))
        right.add_widget(Label(text="sustained", font_size="11sp", color=MUTED))
        vals.add_widget(right)
        root.add_widget(vals)

        root.add_widget(BoxLayout(size_hint_y=None, height=16))

        self.slider = Slider(min=15, max=50, value=30, step=1,
                             size_hint_y=None, height=44)
        self.slider.bind(value=self._on_slide)
        root.add_widget(self.slider)

        root.add_widget(Label(text="matches typical POTS thresholds",
                              font_size="12sp", color=MUTED,
                              size_hint_y=None, height=24, halign="center"))

        root.add_widget(BoxLayout(size_hint_y=None, height=16))

        btn = purple_btn("lets go", height=56)
        btn.bind(on_press=self._next)
        root.add_widget(btn)

        root.add_widget(BoxLayout())

        dots = BoxLayout(size_hint_y=None, height=24, spacing=6)
        dots.add_widget(Label(text="○", font_size="14sp", color=MUTED))
        dots.add_widget(Label(text="○", font_size="14sp", color=MUTED))
        dots.add_widget(Label(text="●", font_size="14sp", color=LILAC))
        root.add_widget(dots)

        self.add_widget(root)

    def _on_slide(self, s, v):
        self.spike = int(v)
        self.spike_lbl.text = f"+{self.spike}"

    def _next(self, *a):
        self.on_done(self.spike, 10)


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
        if len(pts) < 2 or self.width == 0:
            return
        mn  = min(pts) - 5
        mx  = max(pts) + 5
        rng = mx - mn or 1
        coords = []
        for i, v in enumerate(pts):
            x = self.x + (i / (len(pts) - 1)) * self.width
            y = self.y + ((v - mn) / rng) * (self.height - 8) + 4
            coords.extend([x, y])
        with self.canvas:
            Color(0.486, 0.227, 0.855, 1)
            Line(points=coords, width=1.5)


# ── Monitor Screen ────────────────────────────────────────────────────────────

class MonitorScreen(Screen):
    def __init__(self, profile, **kwargs):
        super().__init__(name="monitor", **kwargs)
        self.profile       = profile
        self.bpm_history   = deque(maxlen=60)
        self.ble_worker    = None
        self.alert_showing = False
        self._tap_count    = 0
        self._tap_timer    = None

        with self.canvas.before:
            Color(*BG)
            r = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(r, 'pos', v),
                  size=lambda w, v: setattr(r, 'size', v))

        root = BoxLayout(orientation="vertical",
                         padding=[24, 52, 24, 20], spacing=10)

        # ── Top row ──
        top = BoxLayout(size_hint_y=None, height=40)
        self.greeting_lbl = Label(
            text=get_greeting(profile.get("name", "friend")),
            font_size="15sp", color=LILAC,
            halign="left", valign="middle",
        )
        self.greeting_lbl.bind(size=self.greeting_lbl.setter("text_size"))
        top.add_widget(self.greeting_lbl)

        self.profile_btn = Button(
            text=profile.get("name", "?")[0].upper(),
            font_size="14sp",
            size_hint=(None, None), size=(36, 36),
            background_color=(0, 0, 0, 0),
            color=LILAC,
        )
        make_bg(self.profile_btn, DARK2, radius=18)
        self.profile_btn.bind(on_press=self._profile_tap)
        top.add_widget(self.profile_btn)
        root.add_widget(top)

        # ── Status ──
        self.status_lbl = Label(
            text="not connected", font_size="12sp",
            color=MUTED, size_hint_y=None, height=22,
        )
        root.add_widget(self.status_lbl)

        # ── BPM ──
        self.bpm_lbl = Label(
            text="--", font_size="96sp", bold=True,
            color=LAVENDER, size_hint_y=None, height=116,
        )
        root.add_widget(self.bpm_lbl)

        root.add_widget(Label(
            text="BPM", font_size="12sp", color=MUTED,
            size_hint_y=None, height=18,
        ))

        # ── HRV ──
        self.hrv_lbl = Label(
            text="HRV  --  ms", font_size="13sp",
            color=LILAC, size_hint_y=None, height=28,
        )
        root.add_widget(self.hrv_lbl)

        # ── Graph ──
        graph_outer = BoxLayout(size_hint_y=None, height=76, padding=[8, 6])
        make_bg(graph_outer, DARK1, radius=12)
        self.graph_widget = GraphWidget()
        graph_outer.add_widget(self.graph_widget)
        root.add_widget(graph_outer)

        # ── Stats ──
        stat_row = BoxLayout(size_hint_y=None, height=68, spacing=10)

        def stat_box(val, lbl):
            box = BoxLayout(orientation="vertical", spacing=2, padding=[0, 6])
            make_bg(box, DARK1, radius=10)
            v = Label(text=val, font_size="15sp", color=LILAC, bold=True)
            l = Label(text=lbl, font_size="9sp", color=MUTED)
            box.add_widget(v)
            box.add_widget(l)
            return box, v

        r_box, self.stat_rest  = stat_box(str(profile.get("resting", 65)), "resting")
        h_box, self.stat_hrv   = stat_box("--", "HRV ms")
        s_box, self.stat_status = stat_box("--", "status")
        stat_row.add_widget(r_box)
        stat_row.add_widget(h_box)
        stat_row.add_widget(s_box)
        root.add_widget(stat_row)

        # ── Alert slot ──
        self.alert_slot = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=0,
        )
        root.add_widget(self.alert_slot)

        # ── Connect button ──
        self.connect_btn = purple_btn("connect to band", height=56)
        self.connect_btn.bind(on_press=self.start_monitoring)
        root.add_widget(self.connect_btn)

        root.add_widget(BoxLayout())
        self.add_widget(root)
        init_log()

    # ── Developer mode tap handler ──
    def _profile_tap(self, *a):
        self._tap_count += 1
        if self._tap_timer:
            self._tap_timer.cancel()
        if self._tap_count >= 5:
            self._tap_count = 0
            self._open_dev_mode()
        else:
            self._tap_timer = Clock.schedule_once(self._reset_taps, 1.5)

    def _reset_taps(self, *a):
        if self._tap_count > 0 and self._tap_count < 5:
            self.manager.current = "settings"
        self._tap_count = 0

    def _open_dev_mode(self):
        content = BoxLayout(orientation="vertical",
                            padding=[16, 16], spacing=12)
        content.add_widget(Label(
            text="developer mode", font_size="16sp",
            color=LAVENDER, bold=True,
            size_hint_y=None, height=32,
        ))
        content.add_widget(Label(
            text="enter your code", font_size="13sp",
            color=MUTED, size_hint_y=None, height=24,
        ))
        code_input = TextInput(
            hint_text="developer code",
            font_size="16sp",
            size_hint_y=None, height=48,
            background_color=DARK1,
            foreground_color=LAVENDER,
            multiline=False,
        )
        content.add_widget(code_input)

        confirm = purple_btn("unlock", height=48)
        content.add_widget(confirm)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.88, 0.45),
            background_color=BG,
            separator_height=0,
        )

        def check_code(*a):
            if code_input.text.strip() == DEV_CODE:
                popup.dismiss()
                self._open_scenario_picker()
            else:
                code_input.hint_text = "wrong code — try again"
                code_input.text = ""

        confirm.bind(on_press=check_code)
        popup.open()

    def _open_scenario_picker(self):
        scenarios = ["resting", "walking", "pots_spike", "sustained", "recovery"]
        content = BoxLayout(orientation="vertical",
                            padding=[16, 16], spacing=10)
        content.add_widget(Label(
            text="pick a scenario", font_size="16sp",
            color=LAVENDER, bold=True,
            size_hint_y=None, height=32,
        ))

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.88, 0.72),
            background_color=BG,
            separator_height=0,
        )

        for s in scenarios:
            btn = purple_btn(s, height=48, font=14)
            def make_handler(scenario):
                def handler(*a):
                    popup.dismiss()
                    self._restart_simulator(scenario)
                return handler
            btn.bind(on_press=make_handler(s))
            content.add_widget(btn)

        cancel = ghost_btn("cancel")
        cancel.bind(on_press=popup.dismiss)
        content.add_widget(cancel)
        popup.open()

    def _restart_simulator(self, scenario):
        if self.ble_worker:
            self.ble_worker.stop()
        self.bpm_history.clear()
        self.alert_showing = False
        self.alert_slot.clear_widgets()
        self.alert_slot.height = 0
        self.status_lbl.text = f"simulator: {scenario}"
        self.ble_worker = FakeBLEWorker(
            on_bpm=self.update_bpm,
            on_status=self.update_status,
            on_alert=self.trigger_alert,
            scenario=scenario,
        )
        self.ble_worker.start()

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
        color = LAVENDER if bpm < 90 else FUCHSIA if bpm < 110 else RED
        Animation(color=color, duration=0.4).start(self.bpm_lbl)
        if rmssd:
            self.hrv_lbl.text = f"HRV  {rmssd:.0f}  ms"
            self.stat_hrv.text = f"{rmssd:.0f}"
        self.bpm_history.append(bpm)
        self.graph_widget.update(list(self.bpm_history))
        if bpm < 100 and not self.alert_showing:
            self.stat_status.text  = "clear"
            self.stat_status.color = GREEN

    def trigger_alert(self, alert):
        if self.alert_showing:
            return
        self.alert_showing = True
        self.stat_status.text  = "alert"
        self.stat_status.color = RED

        card = BoxLayout(
            orientation="vertical",
            padding=[14, 12, 14, 12], spacing=8,
            size_hint_y=None, height=0,
        )
        make_bg(card, (0.102, 0.051, 0.180, 1), radius=14)
        card.add_widget(Label(
            text="spike detected" if alert.type == "spike" else "sustained HR",
            font_size="13sp", color=LILAC, bold=True,
            size_hint_y=None, height=26, halign="left",
        ))
        card.add_widget(Label(
            text=alert.message, font_size="11sp", color=MUTED,
            text_size=(Window.width - 90, None),
            halign="left", size_hint_y=None, height=40,
        ))
        dismiss = purple_btn("ok - resting now", height=40, font=12)
        dismiss.bind(on_press=lambda *a: self.dismiss_alert(card))
        card.add_widget(dismiss)

        self.alert_slot.add_widget(card)
        Animation(height=120, duration=0.35).start(card)
        Animation(height=120, duration=0.35).start(self.alert_slot)

        try:
            from plyer import vibrator
            vibrator.vibrate(time=1.5)
        except Exception:
            pass

    def dismiss_alert(self, card):
        def remove(*a):
            self.alert_slot.clear_widgets()
            self.alert_slot.height = 0
        anim = Animation(height=0, duration=0.25)
        anim.bind(on_complete=remove)
        anim.start(card)
        self.alert_showing = False
        self.stat_status.text  = "recovering"
        self.stat_status.color = FUCHSIA

    def open_settings(self, *a):
        self.manager.current = "settings"


# ── Settings Screen ───────────────────────────────────────────────────────────

class SettingsScreen(Screen):
    def __init__(self, profile, **kwargs):
        super().__init__(name="settings", **kwargs)
        self.profile = profile
        with self.canvas.before:
            Color(*BG)
            r = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(r, 'pos', v),
                  size=lambda w, v: setattr(r, 'size', v))

        root = BoxLayout(orientation="vertical",
                         padding=[24, 56, 24, 24], spacing=12)

        back = ghost_btn("back", height=32)
        back.bind(on_press=lambda *a: setattr(self.manager, 'current', 'monitor'))
        root.add_widget(back)

        root.add_widget(Label(
            text="profile", font_size="22sp", color=LAVENDER,
            bold=True, size_hint_y=None, height=44, halign="left",
        ))

        for lbl, val in [
            ("name",             profile.get("name", "")),
            ("resting BPM",      str(profile.get("resting", 65))),
            ("alert threshold",  f"{profile.get('threshold', 110)} BPM"),
            ("spike delta",      f"+{profile.get('spike', 30)} BPM"),
            ("vibration",        "on"),
            ("sound alerts",     "on"),
        ]:
            row = BoxLayout(size_hint_y=None, height=52, padding=[16, 0])
            make_bg(row, DARK1, radius=10)
            row.add_widget(Label(text=lbl, font_size="14sp",
                                 color=LAVENDER, halign="left"))
            row.add_widget(Label(text=val, font_size="14sp",
                                 color=LILAC, halign="right"))
            root.add_widget(row)

        root.add_widget(BoxLayout())

        save = purple_btn("back to monitor")
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
        self._pt = {}
        self.sm.add_widget(Step1Screen(on_done=self._s1))
        self.sm.add_widget(Step2Screen(on_done=self._s2))
        self.sm.add_widget(Step3Screen(on_done=self._s3))
        self.sm.current = "step1"

    def _s1(self, name):
        self._pt["name"] = name
        self.sm.current = "step2"

    def _s2(self, resting, threshold):
        self._pt["resting"]   = resting
        self._pt["threshold"] = threshold
        self.sm.current = "step3"

    def _s3(self, spike, sustained):
        self._pt["spike"]     = spike
        self._pt["sustained"] = sustained
        save_profile(self._pt)
        self._launch_monitor(self._pt)

    def _launch_monitor(self, profile):
        if not self.sm.has_screen("monitor"):
            self.sm.add_widget(MonitorScreen(profile=profile))
        if not self.sm.has_screen("settings"):
            self.sm.add_widget(SettingsScreen(profile=profile))
        self.sm.current = "monitor"


if __name__ == "__main__":
    PaceRingApp().run()
