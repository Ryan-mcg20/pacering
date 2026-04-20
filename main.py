"""
PaceRing: Advanced Heart Rate & POTS Monitoring Application
-----------------------------------------------------------
This is a comprehensive, production-ready implementation featuring:
- Asynchronous BLE (Bluetooth Low Energy) integration via Bleak
- Local SQLite data persistence for historical tracking
- Advanced realtime graphing with Kivy canvas instructions
- Custom UI components with dynamic styling and animations
- Stateful screen management and onboarding flows
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from collections import deque
import random
import math

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle, Mesh
from kivy.animation import Animation
from kivy.utils import get_color_from_hex

# Try importing hardware specific libraries
try:
    from plyer import vibrator
    HAS_VIBRATOR = True
except ImportError:
    HAS_VIBRATOR = False

try:
    from bleak import BleakScanner, BleakClient
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

APP_VERSION = "2.1.0"
PROFILE_FILE = "pacering_profile.json"
DB_FILE = "pacering_data.db"
USE_SIMULATOR = not HAS_BLEAK  # Fallback to simulator if bleak is missing

# BLE UUIDs standard for Heart Rate Service
HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# Advanced Color Palette
COLORS = {
    "bg": get_color_from_hex("#100D1A"),          # Deep Navy/Purple Base
    "surface": get_color_from_hex("#1E1630"),     # Elevated Surface
    "surface_light": get_color_from_hex("#2D2147"),
    "primary": get_color_from_hex("#6C2BEA"),     # Vibrant Purple
    "primary_dark": get_color_from_hex("#4E1AAB"),
    "text_main": get_color_from_hex("#EDE9FE"),   # Lavender White
    "text_muted": get_color_from_hex("#6D5F9F"),  # Muted Purple
    "accent": get_color_from_hex("#A78FE0"),      # Soft Lilac
    "success": get_color_from_hex("#4CE366"),     # Vibrant Green
    "warning": get_color_from_hex("#F59E0B"),     # Amber
    "danger": get_color_from_hex("#F43F53"),      # Crimson Red
    "transparent": (0, 0, 0, 0)
}

FONTS = {
    "h1": "32sp", "h2": "24sp", "h3": "18sp",
    "body": "15sp", "small": "12sp", "micro": "10sp",
    "giant": "96sp"
}

# =============================================================================
# DATA MANAGEMENT & ANALYTICS
# =============================================================================

class DatabaseManager:
    """Handles local SQLite storage for historical HR data and spikes."""
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS hr_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                bpm INTEGER,
                rmssd REAL,
                status TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS spikes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                peak_bpm INTEGER,
                duration_seconds INTEGER
            )
        ''')
        self.conn.commit()

    def log_heart_rate(self, bpm, rmssd, status):
        self.cursor.execute('''
            INSERT INTO hr_logs (bpm, rmssd, status) VALUES (?, ?, ?)
        ''', (bpm, rmssd, status))
        self.conn.commit()

    def log_spike(self, peak_bpm, duration):
        self.cursor.execute('''
            INSERT INTO spikes (peak_bpm, duration_seconds) VALUES (?, ?)
        ''', (peak_bpm, duration))
        self.conn.commit()

class HeartRateAnalyzer:
    """Processes raw RR intervals into actionable metrics (HRV, RMSSD, Spikes)."""
    def __init__(self, config):
        self.config = config
        self.rr_history = deque(maxlen=60)
        self.bpm_history = deque(maxlen=300)
        self.is_spiking = False
        self.spike_start_time = None

    def process_data(self, bpm, rr_intervals):
        self.bpm_history.append(bpm)
        for rr in rr_intervals:
            self.rr_history.append(rr)

        rmssd = self._calculate_rmssd()
        status, alert_msg = self._check_thresholds(bpm)
        return rmssd, status, alert_msg

    def _calculate_rmssd(self):
        if len(self.rr_history) < 2:
            return 0.0
        diffs = [self.rr_history[i] - self.rr_history[i-1] for i in range(1, len(self.rr_history))]
        squared_diffs = [d**2 for d in diffs]
        return math.sqrt(sum(squared_diffs) / len(squared_diffs)) * 1000 # Convert to ms

    def _check_thresholds(self, bpm):
        threshold = self.config.get("threshold", 110)
        spike_delta = self.config.get("spike", 30)
        resting = self.config.get("resting", 65)

        if bpm >= threshold or (bpm - resting) >= spike_delta:
            if not self.is_spiking:
                self.is_spiking = True
                self.spike_start_time = datetime.now()
            return "DANGER", f"Spike detected: {bpm} BPM (+{bpm - resting} from resting)"
        
        elif self.is_spiking and bpm < (threshold - 10):
            # Recovery phase
            self.is_spiking = False
            duration = (datetime.now() - self.spike_start_time).seconds if self.spike_start_time else 0
            return "RECOVERY", f"Recovering. Spike lasted {duration}s."
            
        return "STABLE", ""

# =============================================================================
# BLUETOOTH INTEGRATION
# =============================================================================

class BLEManager:
    """Asynchronous BLE Manager bridging Kivy and Bleak."""
    def __init__(self, on_data_callback, on_status_callback):
        self.on_data = on_data_callback
        self.on_status = on_status_callback
        self.client = None
        self.is_running = False
        self.loop = asyncio.get_event_loop()

    async def connect_and_monitor(self):
        self.is_running = True
        self.on_status("Scanning for Heart Rate Monitors...")
        
        try:
            devices = await BleakScanner.discover(timeout=5.0)
            target_device = None
            
            # Look for devices advertising the HR service or common band names
            for d in devices:
                if d.name and ("band" in d.name.lower() or "hr" in d.name.lower() or "polar" in d.name.lower()):
                    target_device = d
                    break

            if not target_device:
                self.on_status("No band found. Make sure it's paired.")
                self.is_running = False
                return

            self.on_status(f"Found {target_device.name}, connecting...")
            
            async with BleakClient(target_device.address) as client:
                self.client = client
                self.on_status("Connected. Authenticating...")
                
                await client.start_notify(HR_MEASUREMENT_UUID, self._notification_handler)
                self.on_status("Monitoring Active")
                
                while self.is_running and client.is_connected:
                    await asyncio.sleep(1.0)
                    
                await client.stop_notify(HR_MEASUREMENT_UUID)
                self.on_status("Disconnected")
                
        except Exception as e:
            self.on_status(f"BLE Error: {str(e)}")
            self.is_running = False

    def _notification_handler(self, sender, data):
        # Decode GATT Heart Rate Measurement Characteristic
        flags = data[0]
        is_16_bit = flags & 0x01
        rr_present = (flags >> 4) & 0x01
        
        bpm = int.from_bytes(data[1:3], "little") if is_16_bit else data[1]
        
        rr_intervals = []
        if rr_present:
            offset = 3 if is_16_bit else 2
            for i in range(offset, len(data) - 1, 2):
                # HR format gives RR in 1/1024 of a second
                rr = int.from_bytes(data[i:i+2], "little") / 1024.0
                rr_intervals.append(rr)
                
        # Send back to main Kivy thread
        Clock.schedule_once(lambda dt: self.on_data(bpm, rr_intervals), 0)

    def stop(self):
        self.is_running = False

# =============================================================================
# CUSTOM UI WIDGETS
# =============================================================================

def apply_background(widget, color, radius=16, border_color=None, border_width=1):
    """Utility to attach a responsive colored background to any widget."""
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
        line = None
        if border_color:
            Color(*border_color)
            line = Line(rounded_rectangle=(widget.x, widget.y, widget.width, widget.height, radius), width=border_width)

    def _update_rect(instance, value):
        rect.pos = instance.pos
        rect.size = instance.size
        if line:
            line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, radius)

    widget.bind(pos=_update_rect, size=_update_rect)
    return rect

class StyledButton(Button):
    def __init__(self, text, style="primary", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = FONTS["body"]
        self.bold = True
        self.background_color = COLORS["transparent"]
        self.background_normal = ""
        self.size_hint_y = None
        self.height = 56
        
        bg_color = COLORS["primary"] if style == "primary" else COLORS["surface"]
        self.text_color = COLORS["text_main"] if style == "primary" else COLORS["text_muted"]
        self.color = self.text_color
        
        apply_background(self, bg_color, radius=14)
        
        self.bind(state=self.on_state_change)
        
    def on_state_change(self, instance, value):
        if value == "down":
            self.color = COLORS["primary"]
        else:
            self.color = self.text_color

class AdvancedGraphWidget(BoxLayout):
    """A highly performant graph drawing a moving line with a gradient-like fill."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = []
        self.max_points = 60
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_data(self, data_list):
        self.history = list(data_list)[-self.max_points:]
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.clear()
        if len(self.history) < 2 or self.width == 0 or self.height == 0:
            return

        min_val = min(min(self.history) - 10, 50)
        max_val = max(max(self.history) + 10, 150)
        range_val = max_val - min_val

        points = []
        fill_vertices = []
        fill_indices = []

        step_x = self.width / max(1, (len(self.history) - 1))

        # Bottom corners for the polygon fill
        fill_vertices.extend([self.x, self.y, 0, 0])
        fill_indices.append(0)

        for i, val in enumerate(self.history):
            px = self.x + (i * step_x)
            py = self.y + ((val - min_val) / range_val) * self.height
            points.extend([px, py])
            
            fill_vertices.extend([px, py, 0, 0])
            fill_indices.append(i + 1)

        # Complete the polygon back to bottom right
        fill_vertices.extend([points[-2], self.y, 0, 0])
        fill_indices.append(len(self.history) + 1)

        with self.canvas:
            # Draw subtle grid lines
            Color(*COLORS["surface_light"])
            Line(points=[self.x, self.y + self.height/2, self.right, self.y + self.height/2], width=1)
            
            # Draw Fill Mesh (semi-transparent)
            Color(COLORS["primary"][0], COLORS["primary"][1], COLORS["primary"][2], 0.2)
            Mesh(vertices=fill_vertices, indices=fill_indices, mode='triangle_fan')
            
            # Draw actual line
            Color(*COLORS["primary"])
            Line(points=points, width=2, cap='round', joint='round')

# =============================================================================
# SCREENS & FLOWS
# =============================================================================

class BaseScreen(Screen):
    """Base screen applying the standard app background."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        apply_background(self, COLORS["bg"], radius=0)

class OnboardingScreen(BaseScreen):
    def __init__(self, on_complete, **kwargs):
        super().__init__(name="onboarding", **kwargs)
        self.on_complete = on_complete
        self.step = 1
        self.profile_data = {}
        
        self.main_layout = BoxLayout(orientation="vertical", padding=40, spacing=20)
        self.add_widget(self.main_layout)
        self.render_step_1()

    def render_step_1(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(Label(text="step 1 of 3", color=COLORS["accent"], size_hint_y=None, height=30))
        self.main_layout.add_widget(Label(text="What's your name?", font_size=FONTS["h1"], bold=True, color=COLORS["text_main"], size_hint_y=None, height=50))
        self.main_layout.add_widget(Label(text="Personalize your experience.", color=COLORS["text_muted"], size_hint_y=None, height=30))
        
        self.name_input = TextInput(
            hint_text="Enter your name", multiline=False, size_hint_y=None, height=60,
            background_color=COLORS["surface"], foreground_color=COLORS["text_main"], 
            padding=[20, 20], cursor_color=COLORS["primary"]
        )
        self.main_layout.add_widget(self.name_input)
        self.main_layout.add_widget(BoxLayout()) # Flexible spacer
        
        btn = StyledButton("Continue", style="primary")
        btn.bind(on_press=self.process_step_1)
        self.main_layout.add_widget(btn)

    def process_step_1(self, instance):
        name = self.name_input.text.strip()
        if not name:
            name = "Friend"
        self.profile_data["name"] = name
        self.render_step_2()

    def render_step_2(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(Label(text="step 2 of 3", color=COLORS["accent"], size_hint_y=None, height=30))
        self.main_layout.add_widget(Label(text="Resting Heart Rate", font_size=FONTS["h1"], bold=True, size_hint_y=None, height=50))
        
        self.bpm_label = Label(text="65", font_size=FONTS["giant"], color=COLORS["primary"], bold=True, size_hint_y=None, height=120)
        self.main_layout.add_widget(self.bpm_label)
        
        slider = Slider(min=40, max=100, value=65, step=1, size_hint_y=None, height=50, cursor_image='', cursor_size=(30,30))
        slider.bind(value=lambda inst, val: setattr(self.bpm_label, 'text', str(int(val))))
        self.main_layout.add_widget(slider)
        
        self.main_layout.add_widget(BoxLayout()) 
        btn = StyledButton("Continue")
        btn.bind(on_press=lambda inst: self.process_step_2(int(slider.value)))
        self.main_layout.add_widget(btn)

    def process_step_2(self, resting_bpm):
        self.profile_data["resting"] = resting_bpm
        self.render_step_3()

    def render_step_3(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(Label(text="step 3 of 3", color=COLORS["accent"], size_hint_y=None, height=30))
        self.main_layout.add_widget(Label(text="Spike Sensitivity", font_size=FONTS["h1"], bold=True, size_hint_y=None, height=50))
        
        self.spike_label = Label(text="+30 BPM", font_size=FONTS["h2"], color=COLORS["primary"], bold=True, size_hint_y=None, height=80)
        self.main_layout.add_widget(self.spike_label)
        
        slider = Slider(min=15, max=60, value=30, step=5, size_hint_y=None, height=50)
        slider.bind(value=lambda inst, val: setattr(self.spike_label, 'text', f"+{int(val)} BPM"))
        self.main_layout.add_widget(slider)
        
        self.main_layout.add_widget(BoxLayout()) 
        btn = StyledButton("Complete Setup")
        btn.bind(on_press=lambda inst: self.finalize_setup(int(slider.value)))
        self.main_layout.add_widget(btn)

    def finalize_setup(self, spike_val):
        self.profile_data["spike"] = spike_val
        self.profile_data["threshold"] = self.profile_data["resting"] + spike_val
        
        with open(PROFILE_FILE, 'w') as f:
            json.dump(self.profile_data, f)
            
        self.on_complete(self.profile_data)


class DashboardScreen(BaseScreen):
    def __init__(self, profile, **kwargs):
        super().__init__(name="dashboard", **kwargs)
        self.profile = profile
        self.db = DatabaseManager()
        self.analyzer = HeartRateAnalyzer(self.profile)
        self.history = deque(maxlen=60)
        self.sim_event = None
        self.ble_task = None
        
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[25, 50, 25, 25], spacing=20)
        
        # --- HEADER ---
        header = BoxLayout(size_hint_y=None, height=60)
        greeting = self._get_greeting()
        header_text = BoxLayout(orientation="vertical")
        header_text.add_widget(Label(text=f"{greeting},", font_size=FONTS["body"], color=COLORS["text_muted"], halign="left", text_size=(Window.width, None)))
        header_text.add_widget(Label(text=self.profile.get("name", "User"), font_size=FONTS["h2"], bold=True, color=COLORS["text_main"], halign="left", text_size=(Window.width, None)))
        header.add_widget(header_text)
        
        settings_btn = Button(text="⚙", font_size="24sp", size_hint=(None, None), size=(50, 50), background_color=COLORS["transparent"], color=COLORS["text_muted"])
        apply_background(settings_btn, COLORS["surface"], radius=25)
        settings_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        header.add_widget(settings_btn)
        root.add_widget(header)

        # --- STATUS PILL ---
        self.status_pill = BoxLayout(size_hint=(None, None), size=(150, 30), pos_hint={'center_x': 0.5})
        apply_background(self.status_pill, COLORS["surface_light"], radius=15)
        self.status_label = Label(text="Disconnected", font_size=FONTS["micro"], color=COLORS["text_muted"])
        self.status_pill.add_widget(self.status_label)
        root.add_widget(self.status_pill)

        # --- MAIN BPM DISPLAY ---
        bpm_container = BoxLayout(orientation="vertical", size_hint_y=None, height=180)
        self.bpm_val_label = Label(text="--", font_size=FONTS["giant"], bold=True, color=COLORS["text_main"])
        self.bpm_sub_label = Label(text="BPM", font_size=FONTS["small"], color=COLORS["text_muted"], size_hint_y=None, height=20)
        bpm_container.add_widget(self.bpm_val_label)
        bpm_container.add_widget(self.bpm_sub_label)
        root.add_widget(bpm_container)

        # --- GRAPH ---
        graph_wrapper = BoxLayout(size_hint_y=None, height=120, padding=10)
        apply_background(graph_wrapper, COLORS["surface"], radius=16)
        self.graph = AdvancedGraphWidget()
        graph_wrapper.add_widget(self.graph)
        root.add_widget(graph_wrapper)

        # --- STATS ROW ---
        stats_row = BoxLayout(size_hint_y=None, height=90, spacing=15)
        
        self.stat_rest = self._create_stat_card("Resting", str(self.profile.get("resting")), "BPM")
        self.stat_hrv = self._create_stat_card("HRV (RMSSD)", "--", "ms")
        self.stat_state = self._create_stat_card("State", "Clear", "")
        
        stats_row.add_widget(self.stat_rest)
        stats_row.add_widget(self.stat_hrv)
        stats_row.add_widget(self.stat_state)
        root.add_widget(stats_row)

        # --- CONNECT BUTTON ---
        root.add_widget(BoxLayout()) # Spacer
        self.connect_btn = StyledButton("Connect Band", style="primary")
        self.connect_btn.bind(on_press=self.toggle_connection)
        root.add_widget(self.connect_btn)

        self.add_widget(root)

    def _create_stat_card(self, title, val, unit):
        card = BoxLayout(orientation="vertical", padding=10)
        apply_background(card, COLORS["surface"], radius=12)
        val_lbl = Label(text=val, font_size=FONTS["h3"], bold=True, color=COLORS["text_main"])
        title_lbl = Label(text=f"{title} {unit}", font_size=FONTS["micro"], color=COLORS["text_muted"])
        card.add_widget(val_lbl)
        card.add_widget(title_lbl)
        card.val_lbl = val_lbl # Store reference for updates
        return card

    def _get_greeting(self):
        hour = datetime.now().hour
        if hour < 12: return "Good Morning"
        if hour < 17: return "Good Afternoon"
        return "Good Evening"

    def update_ui_from_data(self, bpm, rr_intervals):
        # Process logic
        rmssd, status, alert_msg = self.analyzer.process_data(bpm, rr_intervals)
        
        # Logging
        self.db.log_heart_rate(bpm, rmssd, status)
        
        # UI Updates
        self.bpm_val_label.text = str(bpm)
        self.stat_hrv.val_lbl.text = f"{int(rmssd)}" if rmssd > 0 else "--"
        self.history.append(bpm)
        self.graph.update_data(self.history)

        # State Handling & Animations
        if status == "DANGER":
            self._trigger_alert_ui(bpm)
        elif status == "RECOVERY":
            self.stat_state.val_lbl.text = "Recovery"
            self.stat_state.val_lbl.color = COLORS["warning"]
            self.bpm_val_label.color = COLORS["warning"]
        else:
            self.stat_state.val_lbl.text = "Clear"
            self.stat_state.val_lbl.color = COLORS["success"]
            self.bpm_val_label.color = COLORS["text_main"]

    def _trigger_alert_ui(self, bpm):
        self.stat_state.val_lbl.text = "SPIKE"
        self.stat_state.val_lbl.color = COLORS["danger"]
        
        # Pulse animation on BPM
        anim = Animation(color=COLORS["danger"], duration=0.2) + Animation(color=COLORS["text_main"], duration=0.2)
        anim.start(self.bpm_val_label)
        
        if HAS_VIBRATOR:
            try:
                vibrator.vibrate(time=0.5)
            except Exception:
                pass

    def toggle_connection(self, instance):
        if self.connect_btn.text == "Connect Band":
            self.connect_btn.text = "Disconnect"
            self.connect_btn.background_color = COLORS["surface"]
            self.status_label.text = "Connecting..."
            
            if USE_SIMULATOR:
                self.sim_event = Clock.schedule_interval(self._simulator_tick, 1.0)
            else:
                self.ble_manager = BLEManager(self.update_ui_from_data, self._update_ble_status)
                self.ble_task = asyncio.create_task(self.ble_manager.connect_and_monitor())
        else:
            self.connect_btn.text = "Connect Band"
            self.status_label.text = "Disconnected"
            if self.sim_event:
                self.sim_event.cancel()
            if not USE_SIMULATOR and self.ble_manager:
                self.ble_manager.stop()

    def _update_ble_status(self, msg):
        self.status_label.text = msg

    def _simulator_tick(self, dt):
        """Generates realistic synthetic HRV and BPM data."""
        base_hr = self.profile.get("resting", 65)
        
        # 10% chance to simulate a POTS spike
        if random.random() > 0.9:
            val = base_hr + self.profile.get("spike", 30) + random.randint(-5, 15)
        else:
            val = base_hr + random.randint(-3, 8)
            
        # Generate synthetic RR intervals matching the BPM
        rr_base = 60.0 / val
        rr_intervals = [rr_base + random.uniform(-0.05, 0.05) for _ in range(random.randint(1, 3))]
        
        self.update_ui_from_data(val, rr_intervals)

class SettingsScreen(BaseScreen):
    def __init__(self, profile, **kwargs):
        super().__init__(name="settings", **kwargs)
        self.profile = profile
        
        layout = BoxLayout(orientation="vertical", padding=30, spacing=20)
        
        top = BoxLayout(size_hint_y=None, height=50)
        back_btn = Button(text="< Back", font_size=FONTS["body"], size_hint_x=None, width=80, background_color=COLORS["transparent"], color=COLORS["primary"])
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        top.add_widget(back_btn)
        top.add_widget(Label(text="Settings", font_size=FONTS["h2"], bold=True, halign="right", text_size=(Window.width-140, None)))
        layout.add_widget(top)
        
        # Profile Data Readonly list
        for key, val in self.profile.items():
            row = BoxLayout(size_hint_y=None, height=60, padding=[20, 0])
            apply_background(row, COLORS["surface"], radius=10)
            row.add_widget(Label(text=key.capitalize(), color=COLORS["text_muted"], halign="left"))
            row.add_widget(Label(text=str(val), color=COLORS["text_main"], bold=True, halign="right"))
            layout.add_widget(row)
            
        layout.add_widget(BoxLayout()) # Spacer
        
        reset_btn = StyledButton("Reset Profile", style="secondary")
        reset_btn.color = COLORS["danger"]
        reset_btn.bind(on_press=self.reset_app)
        layout.add_widget(reset_btn)
        
        self.add_widget(layout)

    def reset_app(self, instance):
        if os.path.exists(PROFILE_FILE):
            os.remove(PROFILE_FILE)
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        App.get_running_app().stop()

# =============================================================================
# MAIN APP ARCHITECTURE
# =============================================================================

class PaceRingApp(App):
    def build(self):
        Window.clearcolor = COLORS["bg"]
        self.sm = ScreenManager(transition=FadeTransition())
        
        # Load profile or start onboarding
        profile = self.load_profile()
        if profile:
            self.sm.add_widget(DashboardScreen(profile=profile))
            self.sm.add_widget(SettingsScreen(profile=profile))
            self.sm.current = "dashboard"
        else:
            self.sm.add_widget(OnboardingScreen(on_complete=self.finish_onboarding))
            self.sm.current = "onboarding"
            
        return self.sm

    def load_profile(self):
        if os.path.exists(PROFILE_FILE):
            try:
                with open(PROFILE_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def finish_onboarding(self, profile):
        self.sm.add_widget(DashboardScreen(profile=profile))
        self.sm.add_widget(SettingsScreen(profile=profile))
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "dashboard"

# =============================================================================
# ENTRY POINT WITH ASYNCIO INTEGRATION
# =============================================================================

if __name__ == "__main__":
    # If using bleak, we must run the Kivy app inside an asyncio event loop
    if HAS_BLEAK:
        loop = asyncio.get_event_loop()
        app = PaceRingApp()
        
        async def run_kivy(app):
            await app.async_run()
            
        try:
            loop.run_until_complete(run_kivy(app))
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
    else:
        # Standard synchronous fallback if Bleak is not installed
        PaceRingApp().run()
