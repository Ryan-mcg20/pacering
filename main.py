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
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
import random
import time
import asyncio

# Colors - Lavender Palette
BG_COLOR = "#121411"
SURFACE_COLOR = "#1C1C1E"
PRIMARY_PURPLE = "#BD93F9"
ALERT_RED = "#FF5555"
SUCCESS_GREEN = "#50FA7B"
TEXT_WHITE = "#F8F8F2"
TEXT_GRAY = "#6272A4"

class PaceEngine:
    def __init__(self):
        self.resting_hr = 60
        self.daily_budget = 20.0
        self.current_energy_spent = 0.0
        self.sensitivity_multiplier = 1.0
        self.last_update_time = time.time()

    def update(self, current_hr):
        now = time.time()
        dt = (now - self.last_update_time) / 60.0
        self.last_update_time = now
        k = 2.0 if current_hr > 110 else 1.0
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
        with self.canvas.before:
            self.color_obj = Color(*get_color_from_hex("#FF79C6")[:3], 0.8)
            self.heart_scale = 1.0
            self.ellipse = Ellipse(pos=(self.x + 25, self.y + 25), size=(150, 150))
        self.start_beat()

    def start_beat(self):
        interval = 60.0 / max(1, self.bpm)
        anim = Animation(heart_scale=1.2, duration=interval * 0.3, t='out_quad') + \
               Animation(heart_scale=1.0, duration=interval * 0.7, t='out_bounce')
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
        layout.add_widget(Label(text="PacePoint", font_size='32sp', bold=True, color=get_color_from_hex(PRIMARY_PURPLE)))
        self.name_input = TextInput(text="John Doe", multiline=False, background_color=(.1,.1,.1,1), foreground_color=(1,1,1,1))
        layout.add_widget(Label(text="YOUR NAME", color=get_color_from_hex(TEXT_GRAY)))
        layout.add_widget(self.name_input)
        self.hr_input = TextInput(text="60", multiline=False, background_color=(.1,.1,.1,1), foreground_color=(1,1,1,1))
        layout.add_widget(Label(text="RESTING BPM", color=get_color_from_hex(TEXT_GRAY)))
        layout.add_widget(self.hr_input)
        btn = Button(text="Get Started", background_color=get_color_from_hex(PRIMARY_PURPLE), background_normal='')
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
    energy_progress = NumericProperty(0.0)
    def __init__(self, **kw):
        super().__init__(**kw)
        self.layout = FloatLayout()
        with self.layout.canvas.before:
            Color(*get_color_from_hex(BG_COLOR))
            Rectangle(pos=(0,0), size=(2000, 2000))
        self.header = Label(text="Pace", pos_hint={'top': 0.95, 'center_x': 0.5}, font_size='18sp', bold=True, color=get_color_from_hex(PRIMARY_PURPLE))
        self.layout.add_widget(self.header)
        self.heart = HeartWidget(pos_hint={'center_x': 0.5, 'center_y': 0.65})
        self.layout.add_widget(self.heart)
        self.bpm_label = Label(text="72", font_size='64sp', bold=True, pos_hint={'center_x': 0.5, 'center_y': 0.65})
        self.layout.add_widget(self.bpm_label)
        self.status_label = Label(text="STATUS: OPTIMAL", font_size='14sp', bold=True, pos_hint={'center_x': 0.5, 'center_y': 0.45}, color=get_color_from_hex(SUCCESS_GREEN))
        self.layout.add_widget(self.status_label)
        self.energy_bar = ProgressBar(max=1.0, value=0.0, size_hint=(0.8, None), height=10, pos_hint={'center_x': 0.5, 'y': 0.2})
        self.layout.add_widget(self.energy_bar)
        nav = BoxLayout(size_hint_y=None, height=70, pos_hint={'bottom': 0})
        nav.add_widget(Button(text="Monitor", background_color=(0,0,0,0), color=get_color_from_hex(PRIMARY_PURPLE)))
        s_btn = Button(text="Summary", background_color=(0,0,0,0))
        s_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'summary'))
        nav.add_widget(s_btn)
        self.layout.add_widget(nav)
        self.add_widget(self.layout)

    def on_bpm(self, instance, value):
        self.bpm_label.text = str(int(value))
        self.heart.bpm = value
        self.status_label.text = "STATUS: ELEVATED" if value > 110 else "STATUS: OPTIMAL"
        self.status_label.color = get_color_from_hex(ALERT_RED if value > 110 else SUCCESS_GREEN)

    def on_energy_progress(self, instance, value):
        self.energy_bar.value = value

class SummaryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=20)
        with layout.canvas.before:
            Color(*get_color_from_hex(BG_COLOR))
            Rectangle(pos=(0,0), size=(2000, 2000))
        layout.add_widget(Label(text="Weekly Insights", font_size='24sp', bold=True, color=get_color_from_hex(PRIMARY_PURPLE)))
        btn = Button(text="Back", size_hint_y=None, height=60)
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'monitor'))
        layout.add_widget(btn)
        self.add_widget(layout)

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

if __name__ == '__main__':
    PacePointApp().run()
