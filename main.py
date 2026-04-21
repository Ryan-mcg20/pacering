import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
import random
import time
from datetime import datetime

# -----------------------------------------------------------------------------
# KV DESIGN STRING
# -----------------------------------------------------------------------------
KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

<StyledCard@BoxLayout>:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: get_color_from_hex("#1a1c19")
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(15)]

<MonitorScreen>:
    canvas.before:
        Color:
            rgba: get_color_from_hex("#121411")
        Rectangle:
            pos: self.pos
            size: self.size

    FloatLayout:
        # Greeting & User Name
        Label:
            text: app.get_greeting() + ", " + app.user_name
            font_size: '18sp'
            bold: True
            color: get_color_from_hex("#BD93F9")
            pos_hint: {'top': 0.97, 'x': 0.05}
            size_hint: (None, None)
            size: self.texture_size

        # Heart Centerpiece
        HeartWidget:
            id: heart_widget
            bpm: app.current_bpm
            pos_hint: {'center_x': 0.5, 'center_y': 0.65}
        
        Label:
            text: str(int(app.current_bpm))
            font_size: '80sp'
            bold: True
            color: [1, 1, 1, 1]
            pos_hint: {'center_x': 0.5, 'center_y': 0.65}
        
        Label:
            text: "BPM"
            font_size: '14sp'
            color: get_color_from_hex("#6272A4")
            pos_hint: {'center_x': 0.5, 'center_y': 0.57}

        # Live Graph Card
        StyledCard:
            size_hint: (0.9, 0.2)
            pos_hint: {'center_x': 0.5, 'y': 0.35}
            padding: dp(10)
            Label:
                text: "LIVE CARDIAC RHYTHM"
                font_size: '10sp'
                color: get_color_from_hex("#6272A4")
                size_hint_y: None
                height: dp(20)
            GraphWidget:
                id: graph
                data: app.hr_history
        
        # Energy Budget Panel
        StyledCard:
            size_hint: (0.9, 0.14)
            pos_hint: {'center_x': 0.5, 'y': 0.18}
            
            BoxLayout:
                orientation: 'horizontal'
                Label:
                    text: "ENERGY BUDGET"
                    font_size: '11sp'
                    color: get_color_from_hex("#6272A4")
                    halign: 'left'
                Label:
                    text: str(int(app.daily_budget - app.energy_spent)) + " LEFT"
                    font_size: '11sp'
                    color: get_color_from_hex("#BD93F9")
                    halign: 'right'
            
            ProgressBar:
                max: app.daily_budget
                value: app.energy_spent
                size_hint_y: None
                height: dp(10)

        # Bottom Nav
        BoxLayout:
            size_hint_y: None
            height: dp(70)
            pos_hint: {'bottom': 0}
            canvas.before:
                Color:
                    rgba: get_color_from_hex("#1a1c19")
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            Button:
                text: "MONITOR"
                color: get_color_from_hex("#BD93F9")
                background_color: (0,0,0,0)
            Button:
                text: "SUMMARY"
                color: get_color_from_hex("#6272A4")
                background_color: (0,0,0,0)
                on_press: app.root.current = 'summary'
            Button:
                text: "SETTINGS"
                color: get_color_from_hex("#6272A4")
                background_color: (0,0,0,0)
                on_press: app.root.current = 'settings'

<SummaryScreen>:
    canvas.before:
        Color:
            rgba: get_color_from_hex("#121411")
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(30)
        spacing: dp(20)
        Label:
            text: "Weekly Insights"
            font_size: '28sp'
            bold: True
            color: get_color_from_hex("#BD93F9")
            size_hint_y: None
            height: dp(80)
        
        GridLayout:
            cols: 2
            spacing: dp(15)
            StyledCard:
                Label:
                    text: "AVG BPM"
                    font_size: '11sp'
                Label:
                    text: "72"
                    font_size: '22sp'
                    bold: True
            StyledCard:
                Label:
                    text: "RECOVERY"
                    font_size: '11sp'
                Label:
                    text: "82%"
                    font_size: '22sp'
                    bold: True

        Button:
            text: "BACK TO MONITOR"
            size_hint_y: None
            height: dp(60)
            on_press: app.root.current = 'monitor'

<SettingsScreen>:
    canvas.before:
        Color:
            rgba: get_color_from_hex("#121411")
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(30)
        spacing: dp(20)
        
        Label:
            text: "Profile & Settings"
            font_size: '28sp'
            bold: True
            color: get_color_from_hex("#BD93F9")
            size_hint_y: None
            height: dp(80)

        StyledCard:
            Label:
                text: "USER PROFILE"
                font_size: '12sp'
                color: get_color_from_hex("#6272A4")
                size_hint_y: None
                height: dp(20)
            Label:
                text: "Name: " + app.user_name
                bold: True
            Label:
                text: "Resting HR: " + str(app.resting_hr) + " BPM"
                bold: True
        
        StyledCard:
            Label:
                text: "DEVICE"
                font_size: '12sp'
                color: get_color_from_hex("#6272A4")
                size_hint_y: None
                height: dp(20)
            Label:
                text: "Xiaomi Smart Band 10"
                bold: True
            Label:
                text: "Status: CONNECTED"
                color: get_color_from_hex("#50FA7B")

        Widget: # Spacer
        
        Button:
            text: "SAVE & EXIT"
            size_hint_y: None
            height: dp(60)
            background_color: get_color_from_hex("#BD93F9")
            on_press: app.root.current = 'monitor'
"""

# -----------------------------------------------------------------------------
# WIDGETS
# -----------------------------------------------------------------------------

class HeartWidget(FloatLayout):
    bpm = NumericProperty(72)
    heart_scale = NumericProperty(1.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (260, 260)
        with self.canvas.before:
            self.ring_color = Color(*get_color_from_hex("#BD93F9")[:3], 0.1)
            self.ring = Ellipse(pos=self.pos, size=self.size)
            self.core_color = Color(*get_color_from_hex("#FF79C6")[:3], 0.8)
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
        interval = 60.0 / max(30, self.bpm)
        anim = Animation(heart_scale=1.15, duration=interval * 0.2, t='out_quad') + \
               Animation(heart_scale=0.98, duration=interval * 0.1, t='in_quad') + \
               Animation(heart_scale=1.0, duration=interval * 0.7, t='out_bounce')
        anim.bind(on_complete=lambda *x: self.start_beat())
        anim.start(self)

    def on_heart_scale(self, instance, value):
        self.update_canvas()

class GraphWidget(Widget):
    data = ListProperty([])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(data=self.draw_graph, pos=self.draw_graph, size=self.draw_graph)

    def draw_graph(self, *args):
        self.canvas.clear()
        if not self.data: return
        
        with self.canvas:
            Color(*get_color_from_hex("#BD93F9")[:3], 0.6)
            points = []
            max_val = max(self.data) if self.data else 100
            min_val = min(self.data) if self.data else 60
            span = max(1, max_val - min_val)
            
            w, h = self.size
            dx = w / (len(self.data) - 1) if len(self.data) > 1 else w
            
            for i, val in enumerate(self.data):
                x = self.x + i * dx
                y = self.y + ((val - min_val) / span) * h
                points.extend([x, y])
            
            Line(points=points, width=1.5, joint='round')

# -----------------------------------------------------------------------------
# APP & SCREENS
# -----------------------------------------------------------------------------

class MonitorScreen(Screen):
    pass

class SummaryScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class PacePointApp(App):
    user_name = StringProperty("Ryan")
    current_bpm = NumericProperty(74)
    resting_hr = NumericProperty(60)
    energy_spent = NumericProperty(0.0)
    daily_budget = NumericProperty(20.0)
    hr_history = ListProperty([72, 74, 73, 75, 78, 80, 76, 74, 72, 70])

    def build(self):
        Builder.load_string(KV)
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(MonitorScreen(name='monitor'))
        self.sm.add_widget(SummaryScreen(name='summary'))
        self.sm.add_widget(SettingsScreen(name='settings'))
        
        Clock.schedule_interval(self.update_loop, 1.0)
        return self.sm

    def get_greeting(self):
        hour = datetime.now().hour
        if hour < 12: return "Good morning"
        elif hour < 18: return "Good afternoon"
        else: return "Good evening"

    def update_loop(self, dt):
        # Simulator logic
        target = 74 if self.energy_spent < 15 else 115 # Mock a spike
        if self.current_bpm < target: self.current_bpm += 1
        elif self.current_bpm > target: self.current_bpm -= 1
        self.current_bpm += random.uniform(-1, 1)
        
        # Update history for graph
        self.hr_history.append(self.current_bpm)
        if len(self.hr_history) > 30: self.hr_history.pop(0)
        
        # Energy logic
        k = 2.0 if self.current_bpm > 110 else 1.0
        self.energy_spent += k * (self.current_bpm / self.resting_hr) * (dt / 60.0)

if __name__ == '__main__':
    PacePointApp().run()
