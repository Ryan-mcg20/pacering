"""
POTS Heart Rate Monitor — Main Application
Combines BLE connection, alert engine, and Kivy UI.
"""

import asyncio
import threading
import csv
import os
from datetime import datetime
from collections import deque
from time import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.core.window import Window

# ── Toggle this to switch between simulator and real hardware ─────────────────
USE_SIMULATOR = True   # Set to False when you have Bluetooth

if USE_SIMULATOR:
    from fake_ble import FakeBLEWorker as BLEWorker
else:
    from bleak import BleakScanner, BleakClient
    # BLEWorker is defined later in this file (the real one)

# Import our alert engine
from alert_engine import AlertEngine, AlertConfig, AlertEvent

# BLE UUIDs
HR_SERVICE_UUID   = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# ── Logging setup ─────────────────────────────────────────────────────────────

LOG_FILE = f"hr_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

def init_log():
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "bpm", "rmssd_ms", "alert_type"])

def append_log(bpm: int, rmssd: float | None, alert_type: str = ""):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            bpm,
            f"{rmssd:.1f}" if rmssd else "",
            alert_type,
        ])


# ── BLE Worker (runs in a background thread) ──────────────────────────────────

class RealBLEWorker:
    """
    Manages the BLE connection in a background asyncio event loop.
    Communicates with the UI via thread-safe callbacks.
    """
    def __init__(self, on_bpm, on_status, on_alert):
        self.on_bpm = on_bpm          # Called with (bpm, rmssd)
        self.on_status = on_status    # Called with status string
        self.on_alert = on_alert      # Called with AlertEvent

        self.alert_engine = AlertEngine(AlertConfig(
            sustained_hr_threshold=110,
            sustained_duration_secs=10,
            spike_bpm_delta=30,
            spike_window_secs=30,
        ))
        self._loop = None
        self._client = None
        self._running = False

    def start(self):
        """Kick off the BLE loop in a daemon thread."""
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._ble_main())

    def _parse_hr(self, data: bytearray):
        flags = data[0]
        hr_16bit = flags & 0x01
        rr_present = (flags >> 4) & 0x01
        if hr_16bit:
            bpm = int.from_bytes(data[1:3], byteorder="little")
            rr_start = 3
        else:
            bpm = data[1]
            rr_start = 2
        rr = []
        if rr_present:
            for i in range(rr_start, len(data) - 1, 2):
                rr.append(int.from_bytes(data[i:i+2], byteorder="little") / 1024.0)
        return bpm, rr

    def _notification_handler(self, sender, data: bytearray):
        bpm, rr = self._parse_hr(data)
        alert = self.alert_engine.update(bpm, rr)
        rmssd = self.alert_engine.calculate_rmssd()

        # Schedule UI updates on the main Kivy thread
        Clock.schedule_once(lambda dt: self.on_bpm(bpm, rmssd), 0)
        if alert:
            Clock.schedule_once(lambda dt: self.on_alert(alert), 0)

        append_log(bpm, rmssd, alert.type if alert else "")

    async def _ble_main(self):
        self._running = True
        self.on_status("Scanning for Xiaomi Band...")

        # Scan
        devices = await BleakScanner.discover(timeout=10.0)
        keywords = ["mi band", "xiaomi", "band 10", "mi smart band"]
        address = None
        for d in devices:
            if d.name and any(kw in d.name.lower() for kw in keywords):
                address = d.address
                self.on_status(f"Found: {d.name}")
                break

        if not address:
            self.on_status("Band not found. Ensure it is unpaired from other apps.")
            return

        self.on_status("Connecting...")
        try:
            async with BleakClient(address, timeout=20.0) as client:
                self._client = client
                self.on_status("Connected — monitoring")
                await client.start_notify(HR_MEASUREMENT_UUID, self._notification_handler)
                while self._running and client.is_connected:
                    await asyncio.sleep(0.5)
                await client.stop_notify(HR_MEASUREMENT_UUID)
        except Exception as e:
            self.on_status(f"Connection error: {e}")


# ── Kivy UI ───────────────────────────────────────────────────────────────────

class MonitorScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=12, **kwargs)

        # Status label
        self.status_label = Label(
            text="Not connected",
            font_size="14sp",
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=0.08,
        )
        self.add_widget(self.status_label)

        # Big BPM display
        self.bpm_label = Label(
            text="--",
            font_size="96sp",
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=0.35,
        )
        self.add_widget(self.bpm_label)

        self.add_widget(Label(text="BPM", font_size="18sp", color=(0.7, 0.7, 0.7, 1), size_hint_y=0.06))

        # HRV display
        self.hrv_label = Label(
            text="HRV: --",
            font_size="16sp",
            color=(0.5, 0.8, 0.5, 1),
            size_hint_y=0.07,
        )
        self.add_widget(self.hrv_label)

        # Alert box (hidden until triggered)
        self.alert_label = Label(
            text="",
            font_size="15sp",
            color=(1, 0.3, 0.3, 1),
            text_size=(Window.width - 60, None),
            halign="center",
            size_hint_y=0.15,
        )
        self.add_widget(self.alert_label)

        # Connect button
        self.connect_btn = Button(
            text="Connect to Band",
            font_size="16sp",
            size_hint=(0.7, 0.1),
            pos_hint={"center_x": 0.5},
            background_color=(0.2, 0.5, 0.9, 1),
        )
        self.connect_btn.bind(on_press=self.start_monitoring)
        self.add_widget(self.connect_btn)

        # Log file label
        self.log_label = Label(
            text=f"Logging to: {LOG_FILE}",
            font_size="11sp",
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=0.06,
        )
        self.add_widget(self.log_label)

        self.ble_worker = None
        init_log()

    def start_monitoring(self, instance):
        self.connect_btn.disabled = True
        self.connect_btn.text = "Connecting..."

        self.ble_worker = BLEWorker(
            on_bpm=self.update_bpm,
            on_status=self.update_status,
            on_alert=self.trigger_alert,
            scenario="recovery",
        )
        self.ble_worker.start()

    def update_status(self, status: str):
        self.status_label.text = status

    def update_bpm(self, bpm: int, rmssd: float | None):
        self.bpm_label.text = str(bpm)

        # Colour the number by intensity
        if bpm < 90:
            self.bpm_label.color = (0.3, 0.9, 0.4, 1)   # Green — normal
        elif bpm < 110:
            self.bpm_label.color = (1.0, 0.8, 0.2, 1)   # Amber — elevated
        else:
            self.bpm_label.color = (1.0, 0.3, 0.3, 1)   # Red — high

        if rmssd:
            self.hrv_label.text = f"HRV (RMSSD): {rmssd:.0f} ms"

        # Clear alert if HR has come back down
        if bpm < 100:
            self.alert_label.text = ""

    def trigger_alert(self, alert: AlertEvent):
        self.alert_label.text = f"⚠  {alert.message}"

        try:
            from plyer import vibrator
            vibrator.vibrate(time=1.5)
        except Exception:
            pass

        try:
            from kivy.core.audio import SoundLoader
            sound = SoundLoader.load("alert.wav")
            if sound:
                sound.play()
        except Exception:
            pass

        if alert.type == "spike":
            close_btn = Button(
                text="OK — I'll rest",
                size_hint_y=None,
                height=44,
                background_color=(0.2, 0.5, 0.9, 1),
            )
            content = BoxLayout(orientation="vertical", padding=12, spacing=10)
            content.add_widget(Label(
                text=alert.message,
                text_size=(340, None),
                halign="center",
            ))
            content.add_widget(close_btn)

            popup = Popup(
                title="POTS Alert — Spike Detected",
                content=content,
                size_hint=(0.9, 0.45),
                auto_dismiss=True,
            )
            close_btn.bind(on_press=popup.dismiss)
            popup.open()


class POTSMonitorApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.07, 0.1, 1)  # Dark background
        return MonitorScreen()


if __name__ == "__main__":
    POTSMonitorApp().run()