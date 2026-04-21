import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle, Line
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
import random
import time
import math

# -----------------------------------------------------------------------------
# DESIGN TOKENS (Kinetic Lavender)
# -----------------------------------------------------------------------------
CLR_BG = "#121411"
CLR_SURFACE = "#1a1c19"
CLR_PRIMARY = "#BD93F9"  # Lavender
CLR_SECONDARY = "#FF79C6" # Pinkish accent for heart
CLR_SUCCESS = "#50FA7B"
CLR_ALERT = "#FF5555"
CLR_TEXT = "#F8F8F2"
CLR_TEXT_DIM = "#6272A4"

# Set window background color
Window.clearcolor = get_color_from_hex(CLR_BG)

# -----------------------------------------------------------------------------
# CORE LOGIC: PACE ENGINE
# -----------------------------------------------------------------------------
class PaceEngine:
    def __init__(self):
        self.resting_hr = 60
        self.daily_budget = 20.0
        self.current_energy_spent = 0.0
        self.sensitivity_multiplier = 1.0 
        self.last_update_time = time.time()

    def update(self, current_hr):
        now = time.time()
        dt = (now - self.last_update_time) / 60.0 # minute delta
        self.last_update_time = now
        
        # Pace Logic
        k = 2.0 if current_hr > 110 else 1.0
        cost = k * (current_hr / self.resting_hr) * dt * self.sensitivity_multiplier
        self.current_energy_spent += cost
        
    def get_energy_progress(self):
        return min(1.0, self.current_energy_spent / self.daily_budget)

# -----------------------------------------------------------------------------
# UI COMPONENTS
# -----------------------------------------------------------------------------

class StyledButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = get_color_from_hex(CLR_TEXT)
        self.font_size = '16sp'
        self.bold = True
        with self.canvas.before:
            self.rect_color = Color(*get_color_from_hex(CLR_PRIMARY)[:3], 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class NavButton(Button):
    active = BooleanProperty(False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = get_color_from_hex(CLR_PRIMARY if self.active else CLR_TEXT_DIM)
        self.font_size = '12sp'

class HeartWidget(FloatLayout):
    bpm = NumericProperty(72)
    heart_scale = NumericProperty(1.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (260, 260)
        with self.canvas.before:
            # Outer glow ring
            Color(*get_color_from_hex(CLR_PRIMARY)[:3], 0.1)
            self.ring = Ellipse(pos=self.pos, size=self.size)
            # Inner circle
            self.inner_color = Color(*get_color_from_hex(CLR_SECONDARY)[:3], 0.8)
            self.ellipse = Ellipse(pos=(self.x + 40, self.y + 40), size=(180, 180))
        
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.start_beat()

    def update_canvas(self, *args):
        self.ring.pos = self.pos
        self.ring.size = self.size
        size = 180 * self.heart_scale
        self.ellipse.size = (size, size)
        self.ellipse.pos = (self.center_x - size/2, self.center_y - size/2)

    def start_beat(self):
        # Dynamic duration based on BPM
        interval = 60.0 / max(30, self.bpm)
        anim = Animation(heart_scale=1.15, duration=interval * 0.2, t='out_quad') + \
               Animation(heart_scale=0.98, duration=interval * 0.1, t='in_quad') + \
               Animation(heart_scale=1.0, duration=interval * 0.7, t='out_bounce')
        anim.bind(on_complete=lambda *x: self.start_beat())
        anim.start(self)

    def on_heart_scale(self, instance, value):
        self.update_canvas()

# -----------------------------------------------------------------------------
# SCREENS
# -----------------------------------------------------------------------------

class OnboardingScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=[40, 60, 40, 40], spacing=20)
        
        layout.add_widget(Label(text="PacePoint", font_size='40sp', bold=True, color=get_color_from_hex(CLR_PRIMARY), size_hint_y=None, height=80))
        layout.add_widget(Label(text="Clinical precision for POTS management.", color=get_color_from_hex(CLR_TEXT_DIM), size_hint_y=None, height=40))
        
        layout.add_widget(Label(text="YOUR NAME", color=get_color_from_hex(CLR_TEXT_DIM), size_hint_y=None, height=30, font_size='12sp', halign='left'))
        self.name_input = TextInput(text="User", multiline=False, background_color=(.1, .1, .1, 1), foreground_color=(1, 1, 1, 1), padding=15)
        layout.add_widget(self.name_input)
        
        layout.add_widget(Label(text="RESTING BPM", color=get_color_from_hex(CLR_TEXT_DIM), size_hint_y=None, height=30, font_size='12sp'))
        self.hr_input = TextInput(text="60", multiline=False, background_color=(.1, .1, .1, 1), foreground_color=(1, 1, 1, 1), padding=15)
        layout.add_widget(self.hr_input)
        
        btn = StyledButton(text="BEGIN EXPERIENCE", size_hint_y=None, height=60)
        btn.bind(on_press=self.finish_onboarding)
        layout.add_widget(btn)
        
        self.add_widget(layout)

    def finish_onboarding(self, instance):
        app = App.get_running_app()
        app.user_name = self.name_input.text
        app.engine.resting_hr = int(self.hr_input.text or 60)
        self.manager.current = 'monitor'

class MonitorScreen(Screen):
    bpm = NumericProperty(72)
    energy = NumericProperty(0.0)
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self.main_layout = FloatLayout()
        
        # Header
        self.header = Label(text="Ryan's Pace", pos_hint={'top': 0.96, 'center_x': 0.5}, font_size='18sp', bold=True, color=get_color_from_hex(CLR_PRIMARY))
        self.main_layout.add_widget(self.header)
        
        # Heart Centerpiece
        self.heart = HeartWidget(pos_hint={'center_x': 0.5, 'center_y': 0.65})
        self.main_layout.add_widget(self.heart)
        
        self.bpm_label = Label(text="72", font_size='80sp', bold=True, pos_hint={'center_x': 0.5, 'center_y': 0.65})
        self.main_layout.add_widget(self.bpm_label)
        self.main_layout.add_widget(Label(text="BPM", font_size='14sp', pos_hint={'center_x': 0.5, 'center_y': 0.57}, color=get_color_from_hex(CLR_TEXT_DIM)))

        # Status Badge
        self.status_label = Label(text="PACING OPTIMAL", font_size='12sp', bold=True, pos_hint={'center_x': 0.5, 'center_y': 0.45}, color=get_color_from_hex(CLR_SUCCESS))
        self.main_layout.add_widget(self.status_label)

        # Energy Panel
        self.energy_box = BoxLayout(orientation='vertical', size_hint=(0.85, 0.15), pos_hint={'center_x': 0.5, 'y': 0.18}, padding=20)
        with self.energy_box.canvas.before:
            Color(*get_color_from_hex(CLR_SURFACE)[:3], 1)
            self.energy_bg = RoundedRectangle(pos=self.energy_box.pos, size=self.energy_box.size, radius=[15])
        self.energy_box.bind(pos=self.update_energy_bg, size=self.update_energy_bg)
        
        self.energy_box.add_widget(Label(text="ENERGY BUDGET", font_size='11sp', color=get_color_from_hex(CLR_TEXT_DIM), halign='left'))
        self.pbar = ProgressBar(max=1.0, value=0.0, size_hint_y=None, height=8)
        self.energy_box.add_widget(self.pbar)
        self.main_layout.add_widget(self.energy_box)
        
        # Nav
        nav = BoxLayout(size_hint_y=None, height=70, pos_hint={'bottom': 0})
        m_btn = NavButton(text="MONITOR", active=True)
        s_btn = NavButton(text="SUMMARY")
        s_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'summary'))
        nav.add_widget(m_btn)
        nav.add_widget(s_btn)
        self.main_layout.add_widget(nav)
        
        # Alert Box (Hidden)
        self.alert = FloatLayout(size_hint=(0.9, 0.2), pos_hint={'center_x': 0.5, 'top': 0.92})
        with self.alert.canvas.before:
            Color(*get_color_from_hex(CLR_ALERT)[:3], 0.95)
            self.alert_bg = RoundedRectangle(pos=self.alert.pos, size=self.alert.size, radius=[15])
        self.alert.add_widget(Label(text="WARNING: BRAIN OXYGEN LOW", bold=True, pos_hint={'center_x': 0.5, 'y': 0.6}))
        self.alert.add_widget(Label(text="Sit down immediately.", font_size='14sp', pos_hint={'center_x': 0.5, 'y': 0.4}))
        ack = Button(text="ACKNOWLEDGE", size_hint=(0.6, 0.3), pos_hint={'center_x': 0.5, 'y': 0.1}, background_color=(1,1,1,0.2))
        ack.bind(on_press=lambda x: self.main_layout.remove_widget(self.alert))
        self.alert.add_widget(ack)
        
        self.add_widget(self.main_layout)

    def update_energy_bg(self, *args):
        self.energy_bg.pos = self.energy_box.pos
        self.energy_bg.size = self.energy_box.size

    def on_bpm(self, instance, value):
        self.bpm_label.text = str(int(value))
        self.heart.bpm = value
        if value > 110:
            self.status_label.text = "ELEVATED HEART RATE"
            self.status_label.color = get_color_from_hex(CLR_ALERT)
            if self.alert not in self.main_layout.children:
                self.main_layout.add_widget(self.alert)
        else:
            self.status_label.text = "PACING OPTIMAL"
            self.status_label.color = get_color_from_hex(CLR_SUCCESS)

    def on_energy(self, instance, value):
        self.pbar.value = value

class SummaryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        layout.add_widget(Label(text="Weekly Insights", font_size='28sp', bold=True, color=get_color_from_hex(CLR_PRIMARY), size_hint_y=None, height=80))
        
        grid = GridLayout(cols=2, spacing=15)
        grid.add_widget(self.stat_card("AVG BPM", "72"))
        grid.add_widget(self.stat_card("AVG HRV", "64ms"))
        grid.add_widget(self.stat_card("RECOVERY", "82%"))
        grid.add_widget(self.stat_card("STRESS", "LOW"))
        layout.add_widget(grid)
        
        btn = StyledButton(text="BACK TO MONITOR", size_hint_y=None, height=60)
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'monitor'))
        layout.add_widget(btn)
        self.add_widget(layout)

    def stat_card(self, title, val):
        box = BoxLayout(orientation='vertical', padding=15)
        with box.canvas.before:
            Color(*get_color_from_hex(CLR_SURFACE)[:3], 1)
            RoundedRectangle(pos=box.pos, size=box.size, radius=[12])
        box.add_widget(Label(text=title, font_size='11sp', color=get_color_from_hex(CLR_TEXT_DIM)))
        box.add_widget(Label(text=val, font_size='22sp', bold=True))
        return box

# -----------------------------------------------------------------------------
# APP CLASS
# -----------------------------------------------------------------------------
class PacePointApp(App):
    user_name = StringProperty("User")
    current_bpm = NumericProperty(60)
    target_bpm = NumericProperty(60)

    def build(self):
        self.engine = PaceEngine()
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(OnboardingScreen(name='onboarding'))
        self.sm.add_widget(MonitorScreen(name='monitor'))
        self.sm.add_widget(SummaryScreen(name='summary'))
        
        Clock.schedule_interval(self.update_loop, 1.0)
        return self.sm

    def update_loop(self, dt):
        # Simple Simulator Logic
        if self.current_bpm < self.target_bpm:
            self.current_bpm += min(2, self.target_bpm - self.current_bpm)
        elif self.current_bpm > self.target_bpm:
            self.current_bpm -= min(1, self.current_bpm - self.target_bpm)
        
        self.current_bpm += random.uniform(-0.5, 0.5)
        self.engine.update(self.current_bpm)
        
        mon = self.sm.get_screen('monitor')
        mon.bpm = self.current_bpm
        mon.energy = self.engine.get_energy_progress()
        mon.header.text = f"{self.user_name}'s Pace"

if __name__ == '__main__':
    PacePointApp().run()
