import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.switch import Switch
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
import random
import math
import time

# Colors - Lavender Palette
BG_COLOR = "#121411"
SURFACE_COLOR = "#1C1C1E"
PRIMARY_PURPLE = "#BD93F9" # Lavender accent
ALERT_RED = "#FF5555"
SUCCESS_GREEN = "#50FA7B"
TEXT_WHITE = "#F8F8F2"
TEXT_GRAY = "#6272A4"

class PaceEngine:
    def __init__(self):
        self.resting_hr = 60
        self.daily_budget = 20.0
        self.current_energy_spent = 0.0
        self.sensitivity_multiplier = 1.0 # Default Medium
        self.hr_history = []
        self.last_update_time = time.time()
        self.rr_intervals = []
        self.hrv_history = [65, 62, 68, 60, 64, 63, 64] # 7-day rolling baseline

    def update(self, current_hr):
        now = time.time()
        dt = (now - self.last_update_time) / 60.0 # minute delta
        self.last_update_time = now
        
        # Pace Logic
        k = 1.0
        if current_hr > 110:
            k = 2.0
        
        # Apply sensitivity multiplier to the cost calculation
        cost = k * (current_hr / self.resting_hr) * dt * self.sensitivity_multiplier
        self.current_energy_spent += cost
        
    def get_energy_progress(self):
        return min(1.0, self.current_energy_spent / self.daily_budget)

class HeartWidget(FloatLayout):
    bpm = NumericProperty(72)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (200, 200)
        self.bind(bpm=self.update_animation)
        with self.canvas.before:
            self.color = Color(*get_color_from_hex("#FF79C6")[:3], 0.8) # Pinkish pulse
            self.heart_scale = 1.0
            self.ellipse = Ellipse(pos=(self.x + 25, self.y + 25), size=(150, 150))
        self.start_beat()

    def start_beat(self):
        interval = 60.0 / max(1, self.bpm)
        anim = Animation(heart_scale=1.2, duration=interval * 0.3, t='out_quad') + \
               Animation(heart_scale=0.95, duration=interval * 0.2, t='in_out_quad') + \
               Animation(heart_scale=1.0, duration=interval * 0.5, t='out_bounce')
        anim.bind(on_complete=lambda *x: self.start_beat())
        anim.start(self)

    def on_heart_scale(self, instance, value):
        size = 150 * value
        self.ellipse.size = (size, size)
        self.ellipse.pos = (self.center_x - size/2, self.center_y - size/2)

class OnboardingScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        with layout.canvas.before:
            Color(*get_color_from_hex(BG_COLOR))
            Rectangle(pos=(0,0), size=(2000, 2000))
        
        layout.add_widget(Label(text="PacePoint", font_size='32sp', bold=True, color=get_color_from_hex(PRIMARY_PURPLE), size_hint_y=None, height=100))
        layout.add_widget(Label(text="Setup Pace", font_size='24sp', size_hint_y=None, height=40))
        layout.add_widget(Label(text="Configure your personal profile", color=get_color_from_hex(TEXT_GRAY), size_hint_y=None, height=40))
        
        # Name Input
        layout.add_widget(Label(text="YOUR NAME", size_hint_y=None, height=30, halign='left', color=get_color_from_hex(TEXT_GRAY)))
        self.name_input = TextInput(text="John Doe", multiline=False, background_color=(.1,.1,.1,1), foreground_color=(1,1,1,1), padding=15)
        layout.add_widget(self.name_input)
        
        # HR Input
        layout.add_widget(Label(text="RESTING HEART RATE (BPM)", size_hint_y=None, height=30, color=get_color_from_hex(TEXT_GRAY)))
        self.hr_input = TextInput(text="60", multiline=False, background_color=(.1,.1,.1,1), foreground_color=(1,1,1,1), padding=15)
        layout.add_widget(self.hr_input)
        
        # Sensitivity Selector
        layout.add_widget(Label(text="SENSITIVITY LEVEL", size_hint_y=None, height=30, color=get_color_from_hex(TEXT_GRAY)))
        sens_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.low_sens = ToggleButton(text="Low", group='sens', state='normal')
        self.med_sens = ToggleButton(text="Medium", group='sens', state='down')
        self.high_sens = ToggleButton(text="High", group='sens', state='normal')
        sens_layout.add_widget(self.low_sens)
        sens_layout.add_widget(self.med_sens)
        sens_layout.add_widget(self.high_sens)
        layout.add_widget(sens_layout)
        
        btn = Button(text="Get Started", background_color=get_color_from_hex(PRIMARY_PURPLE), background_normal='', bold=True, size_hint_y=None, height=60)
        btn.bind(on_press=self.finish_onboarding)
        layout.add_widget(btn)
        self.add_widget(layout)

    def finish_onboarding(self, instance):
        app = App.get_running_app()
        app.user_name = self.name_input.text
        app.engine.resting_hr = int(self.hr_input.text or 60)
        
        # Correctly set sensitivity based on toggle state
        if self.low_sens.state == 'down':
            app.engine.sensitivity_multiplier = 0.5
        elif self.high_sens.state == 'down':
            app.engine.sensitivity_multiplier = 1.5
        else:
            app.engine.sensitivity_multiplier = 1.0 # Medium
            
        self.manager.current = 'monitor'

class MonitorScreen(Screen):
    bpm = NumericProperty(72)
    energy_progress = NumericProperty(0.0)
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self.layout = FloatLayout()
        with self.layout.canvas.before:
            Color(*get_color_from_hex(BG_COLOR))
            Rectangle(pos=(0,0), size=(2000, 2000))
            
        # Top Bar
        self.header = Label(text="Ryan's Pace", pos_hint={'top': 0.95, 'center_x': 0.5}, font_size='18sp', bold=True, color=get_color_from_hex(PRIMARY_PURPLE))
        self.layout.add_widget(self.header)
        
        # Heart
        self.heart = HeartWidget(pos_hint={'center_x': 0.5, 'center_y': 0.65})
        self.layout.add_widget(self.heart)
        
        self.bpm_label = Label(text="72", font_size='64sp', bold=True, pos_hint={'center_x': 0.5, 'center_y': 0.65})
        self.layout.add_widget(self.bpm_label)
        self.layout.add_widget(Label(text="BPM", font_size='14sp', pos_hint={'center_x': 0.5, 'center_y': 0.58}, color=get_color_from_hex(TEXT_GRAY)))

        # Status
        self.status_label = Label(text="STATUS: OPTIMAL", font_size='14sp', bold=True, pos_hint={'center_x': 0.5, 'center_y': 0.45}, color=get_color_from_hex(SUCCESS_GREEN))
        self.layout.add_widget(self.status_label)

        # Stats Panel
        stats = BoxLayout(orientation='vertical', padding=20, spacing=15, size_hint=(0.9, 0.2), pos_hint={'center_x': 0.5, 'y': 0.15})
        with stats.canvas.before:
            Color(*get_color_from_hex(SURFACE_COLOR))
            RoundedRectangle(pos=(Window.width*0.05, Window.height*0.15), size=(Window.width*0.9, Window.height*0.2), radius=[15])
            
        stats.add_widget(Label(text="ENERGY BUDGET", font_size='12sp', color=get_color_from_hex(TEXT_GRAY)))
        self.energy_bar = ProgressBar(max=1.0, value=0.0, size_hint_y=None, height=10)
        stats.add_widget(self.energy_bar)
        self.layout.add_widget(stats)
        
        # Navigation
        nav = BoxLayout(size_hint_y=None, height=70, pos_hint={'bottom': 0})
        m_btn = Button(text="Monitor", background_color=(0,0,0,0), color=get_color_from_hex(PRIMARY_PURPLE))
        s_btn = Button(text="Summary", background_color=(0,0,0,0))
        d_btn = Button(text="Dev", background_color=(0,0,0,0))
        s_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'summary'))
        d_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dev'))
        nav.add_widget(m_btn)
        nav.add_widget(s_btn)
        nav.add_widget(d_btn)
        self.layout.add_widget(nav)
        
        # Alert (Hidden by default)
        self.alert_box = BoxLayout(orientation='vertical', size_hint=(0.9, 0.2), pos_hint={'center_x': 0.5, 'top': 0.9}, padding=20)
        with self.alert_box.canvas.before:
            Color(*get_color_from_hex(ALERT_RED))
            RoundedRectangle(pos=self.alert_box.pos, size=self.alert_box.size, radius=[15])
        self.alert_box.add_widget(Label(text="WARNING", bold=True))
        self.alert_box.add_widget(Label(text="Brain Oxygen Dropping. Sit down now."))
        ack_btn = Button(text="Acknowledge", size_hint_y=None, height=40)
        ack_btn.bind(on_press=lambda x: self.hide_alert())
        self.alert_box.add_widget(ack_btn)
        
        self.add_widget(self.layout)

    def on_bpm(self, instance, value):
        self.bpm_label.text = str(int(value))
        self.heart.bpm = value
        if value > 110:
            self.status_label.text = "STATUS: ELEVATED"
            self.status_label.color = get_color_from_hex(ALERT_RED)
        else:
            self.status_label.text = "STATUS: OPTIMAL"
            self.status_label.color = get_color_from_hex(SUCCESS_GREEN)

    def on_energy_progress(self, instance, value):
        self.energy_bar.value = value

    def show_alert(self):
        if self.alert_box not in self.layout.children:
            self.layout.add_widget(self.alert_box)
            
    def hide_alert(self):
        if self.alert_box in self.layout.children:
            self.layout.remove_widget(self.alert_box)

class SummaryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=20)
        with layout.canvas.before:
            Color(*get_color_from_hex(BG_COLOR))
            Rectangle(pos=(0,0), size=(2000, 2000))
            
        layout.add_widget(Label(text="Weekly Insights", font_size='24sp', bold=True, color=get_color_from_hex(PRIMARY_PURPLE), size_hint_y=None, height=80))
        
        stats_grid = GridLayout(cols=2, spacing=15, size_hint_y=0.5)
        stats_grid.add_widget(self.stat_card("AVG BPM", "72"))
        stats_grid.add_widget(self.stat_card("AVG HRV", "64ms"))
        stats_grid.add_widget(self.stat_card("RECOVERY", "82%"))
        stats_grid.add_widget(self.stat_card("STRESS", "LOW"))
        layout.add_widget(stats_grid)
        
        btn = Button(text="Back to Monitor", size_hint_y=None, height=60, background_color=(0,0,0,0), color=get_color_from_hex(PRIMARY_PURPLE))
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'monitor'))
        layout.add_widget(btn)
        self.add_widget(layout)

    def stat_card(self, title, val):
        box = BoxLayout(orientation='vertical', padding=15)
        with box.canvas.before:
            Color(*get_color_from_hex(SURFACE_COLOR))
            RoundedRectangle(pos=box.pos, size=box.size, radius=[10])
        box.add_widget(Label(text=title, font_size='10sp', color=get_color_from_hex(TEXT_GRAY)))
        box.add_widget(Label(text=val, font_size='20sp', bold=True))
        return box

class DevToolsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        with layout.canvas.before:
            Color(*get_color_from_hex(BG_COLOR))
            Rectangle(pos=(0,0), size=(2000, 2000))
            
        layout.add_widget(Label(text="Developer Tools", font_size='22sp', bold=True, color=get_color_from_hex(PRIMARY_PURPLE), size_hint_y=None, height=60))
        
        scenarios = [("Resting", 60), ("Walking", 100), ("POTS Spike", 135), ("Running", 155), ("Recovery", 80)]
        for name, val in scenarios:
            btn = Button(text=name, size_hint_y=None, height=50, background_color=get_color_from_hex(SURFACE_COLOR), background_normal='')
            btn.bind(on_press=lambda x, v=val: self.set_scenario(v))
            layout.add_widget(btn)
            
        btn_back = Button(text="Close", size_hint_y=None, height=60, background_color=get_color_from_hex(PRIMARY_PURPLE), background_normal='')
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'monitor'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def set_scenario(self, val):
        app = App.get_running_app()
        app.target_bpm = val

class PacePointApp(App):
    target_bpm = NumericProperty(60)
    current_bpm = NumericProperty(60)
    user_name = StringProperty("User")
    
    def build(self):
        self.engine = PaceEngine()
        self.sm = ScreenManager()
        self.sm.add_widget(OnboardingScreen(name='onboarding'))
        self.sm.add_widget(MonitorScreen(name='monitor'))
        self.sm.add_widget(SummaryScreen(name='summary'))
        self.sm.add_widget(DevToolsScreen(name='dev'))
        
        Clock.schedule_interval(self.update_loop, 1.0)
        return self.sm

    def update_loop(self, dt):
        if self.current_bpm < self.target_bpm:
            self.current_bpm += min(2, self.target_bpm - self.current_bpm)
        elif self.current_bpm > self.target_bpm:
            self.current_bpm -= min(1, self.current_bpm - self.target_bpm)
        
        self.current_bpm += random.uniform(-0.5, 0.5)
        self.engine.update(self.current_bpm)
        
        mon = self.sm.get_screen('monitor')
        mon.bpm = self.current_bpm
        mon.energy_progress = self.engine.get_energy_progress()
        mon.header.text = f"{self.user_name}'s Pace"
        
        if self.current_bpm > 110:
            mon.show_alert()

if __name__ == '__main__':
    PacePointApp().run()
