import os
import json
import time
import random
from collections import deque
from datetime import datetime

# Kivy imports
from kivy.app import App
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup

# For desktop testing, simulate a mobile screen ratio
Window.size = (400, 800)
Window.clearcolor = get_color_from_hex('#100d1a')

# Configuration
USE_SIMULATOR = True

# --- KIVY UI DEFINITION (KV LANGUAGE) ---
KV = '''
#:import get_color_from_hex kivy.utils.get_color_from_hex

# --- Custom Reusable Widgets ---
<SmoothButton@ButtonBehavior+Label>:
    background_color: get_color_from_hex('#7c3aed')
    color: get_color_from_hex('#ede9fe')
    font_size: '18sp'
    bold: True
    canvas.before:
        Color:
            rgba: self.background_color if self.state == 'normal' else get_color_from_hex('#6c2bda')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]

<GhostButton@ButtonBehavior+Label>:
    color: get_color_from_hex('#6d5fa0')
    font_size: '16sp'

<DarkCard@BoxLayout>:
    canvas.before:
        Color:
            rgba: get_color_from_hex('#0d0b16')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]

<StatBox@BoxLayout>:
    orientation: 'vertical'
    padding: dp(15)
    canvas.before:
        Color:
            rgba: get_color_from_hex('#0d0b16')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]
    value_text: ''
    label_text: ''
    Label:
        text: root.value_text
        font_size: '32sp'
        bold: True
        color: get_color_from_hex('#ede9fe')
    Label:
        text: root.label_text
        font_size: '12sp'
        color: get_color_from_hex('#6d5fa0')
        
<PillBox@BoxLayout>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: get_color_from_hex('#1e1630')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
    value: ''
    label: ''
    color_val: get_color_from_hex('#ede9fe')
    Label:
        text: root.value
        font_size: '16sp'
        bold: True
        color: root.color_val
    Label:
        text: root.label
        font_size: '10sp'
        color: get_color_from_hex('#6d5fa0')

<Dot@Widget>:
    size_hint: None, None
    size: dp(10), dp(10)
    active: False
    canvas.before:
        Color:
            rgba: get_color_from_hex('#7c3aed') if self.active else get_color_from_hex('#1e1630')
        Ellipse:
            pos: self.pos
            size: self.size

# --- Screens ---
<OnboardingNameScreen>:
    FloatLayout:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(30)
            spacing: dp(20)
            
            Label:
                text: 'step 1 of 3'
                color: get_color_from_hex('#e879f9')
                size_hint_y: None
                height: dp(30)
                font_size: '14sp'
                halign: 'center'
                
            Label:
                text: "what's your name?"
                color: get_color_from_hex('#ede9fe')
                font_size: '32sp'
                bold: True
                size_hint_y: None
                height: dp(50)
                
            Label:
                text: "so we can make this feel like yours"
                color: get_color_from_hex('#6d5fa0')
                font_size: '16sp'
                size_hint_y: None
                height: dp(30)
                
            Widget:
                size_hint_y: 0.1
                
            TextInput:
                id: name_input
                hint_text: 'your name'
                background_color: get_color_from_hex('#0d0b16')
                foreground_color: get_color_from_hex('#ede9fe')
                cursor_color: get_color_from_hex('#7c3aed')
                font_size: '20sp'
                padding: [dp(20), dp(15)]
                size_hint_y: None
                height: dp(60)
                multiline: False
                background_normal: ''
                background_active: ''
                canvas.before:
                    Color:
                        rgba: get_color_from_hex('#1e1630')
                    Line:
                        rounded_rectangle: [self.x, self.y, self.width, self.height, 10]
                        width: 1
                
            Widget:
                size_hint_y: 0.5
                
            SmoothButton:
                text: 'continue'
                size_hint_y: None
                height: dp(60)
                on_release: root.next_screen()
                
            BoxLayout:
                size_hint_y: None
                height: dp(20)
                spacing: dp(10)
                pos_hint: {'center_x': 0.5}
                size_hint_x: None
                width: dp(50)
                Dot:
                    active: True
                Dot:
                Dot:

<OnboardingRestingScreen>:
    FloatLayout:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(30)
            spacing: dp(20)
            
            Label:
                text: 'step 2 of 3'
                color: get_color_from_hex('#e879f9')
                size_hint_y: None
                height: dp(30)
                font_size: '14sp'
                
            Label:
                text: "your resting heart rate"
                color: get_color_from_hex('#ede9fe')
                font_size: '30sp'
                bold: True
                size_hint_y: None
                height: dp(50)
                
            Label:
                text: "used to detect spikes accurately"
                color: get_color_from_hex('#6d5fa0')
                font_size: '16sp'
                size_hint_y: None
                height: dp(30)
                
            BoxLayout:
                size_hint_y: None
                height: dp(120)
                spacing: dp(20)
                StatBox:
                    value_text: str(int(rest_slider.value))
                    label_text: 'RESTING BPM'
                StatBox:
                    value_text: str(int(rest_slider.value) + 45)
                    label_text: 'ALERT THRESHOLD'
                    
            Widget:
                size_hint_y: 0.1
                
            Slider:
                id: rest_slider
                min: 40
                max: 100
                value: 65
                step: 1
                cursor_image: ''
                cursor_size: (dp(24), dp(24))
                background_width: dp(4)
                value_track: True
                value_track_color: get_color_from_hex('#7c3aed')
                size_hint_y: None
                height: dp(40)
                
            Label:
                text: "drag to set your resting BPM"
                color: get_color_from_hex('#6d5fa0')
                font_size: '14sp'
                size_hint_y: None
                height: dp(30)
                
            Widget:
                size_hint_y: 0.4
                
            SmoothButton:
                text: 'continue'
                size_hint_y: None
                height: dp(60)
                on_release: root.next_screen()
                
            GhostButton:
                text: 'use defaults'
                size_hint_y: None
                height: dp(40)
                on_release: 
                    rest_slider.value = 65
                    root.next_screen()
                
            BoxLayout:
                size_hint_y: None
                height: dp(20)
                spacing: dp(10)
                pos_hint: {'center_x': 0.5}
                size_hint_x: None
                width: dp(50)
                Dot:
                Dot:
                    active: True
                Dot:

<OnboardingSpikeScreen>:
    FloatLayout:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(30)
            spacing: dp(20)
            
            Label:
                text: 'step 3 of 3'
                color: get_color_from_hex('#e879f9')
                size_hint_y: None
                height: dp(30)
                font_size: '14sp'
                
            Label:
                text: "spike sensitivity"
                color: get_color_from_hex('#ede9fe')
                font_size: '30sp'
                bold: True
                size_hint_y: None
                height: dp(50)
                
            Label:
                text: "alert me when HR rises by..."
                color: get_color_from_hex('#6d5fa0')
                font_size: '16sp'
                size_hint_y: None
                height: dp(30)
                
            BoxLayout:
                size_hint_y: None
                height: dp(120)
                spacing: dp(20)
                StatBox:
                    value_text: "+" + str(int(spike_slider.value))
                    label_text: 'BPM SPIKE'
                StatBox:
                    value_text: "10s"
                    label_text: 'SUSTAINED FOR'
                    
            Widget:
                size_hint_y: 0.1
                
            Slider:
                id: spike_slider
                min: 15
                max: 50
                value: 30
                step: 1
                cursor_image: ''
                cursor_size: (dp(24), dp(24))
                value_track: True
                value_track_color: get_color_from_hex('#7c3aed')
                size_hint_y: None
                height: dp(40)
                
            Label:
                text: "matches typical POTS thresholds"
                color: get_color_from_hex('#6d5fa0')
                font_size: '14sp'
                size_hint_y: None
                height: dp(30)
                
            Widget:
                size_hint_y: 0.4
                
            SmoothButton:
                text: "let's go"
                size_hint_y: None
                height: dp(60)
                on_release: root.finish_onboarding()
                
            BoxLayout:
                size_hint_y: None
                height: dp(20)
                spacing: dp(10)
                pos_hint: {'center_x': 0.5}
                size_hint_x: None
                width: dp(50)
                Dot:
                Dot:
                Dot:
                    active: True

<MainMonitorScreen>:
    FloatLayout:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(25)
            spacing: dp(15)
            
            # Header
            FloatLayout:
                size_hint_y: None
                height: dp(60)
                Label:
                    id: greeting_label
                    text: "good morning,"
                    color: get_color_from_hex('#ede9fe')
                    font_size: '22sp'
                    bold: True
                    halign: 'left'
                    text_size: self.size
                    valign: 'middle'
                    pos_hint: {'x': 0, 'center_y': 0.5}
                
                ButtonBehavior:
                    id: profile_btn
                    size_hint: None, None
                    size: dp(45), dp(45)
                    pos_hint: {'right': 1, 'center_y': 0.5}
                    on_release: root.handle_profile_tap()
                    Label:
                        id: profile_initial
                        text: "R"
                        font_size: '20sp'
                        bold: True
                        color: get_color_from_hex('#ede9fe')
                        center: self.parent.center
                        canvas.before:
                            Color:
                                rgba: get_color_from_hex('#7c3aed')
                            Ellipse:
                                pos: self.parent.pos
                                size: self.parent.size

            Label:
                id: status_label
                text: "connected — monitoring"
                color: get_color_from_hex('#6d5fa0')
                font_size: '14sp'
                halign: 'left'
                text_size: self.size
                size_hint_y: None
                height: dp(20)

            Widget:
                size_hint_y: 0.1

            # Center Giant BPM
            FloatLayout:
                size_hint_y: None
                height: dp(180)
                Label:
                    id: bpm_label
                    text: "--"
                    font_size: '96sp'
                    bold: True
                    color: get_color_from_hex('#ede9fe')
                    pos_hint: {'center_x': 0.5, 'center_y': 0.6}
                
                Label:
                    text: "BPM"
                    font_size: '18sp'
                    color: get_color_from_hex('#6d5fa0')
                    pos_hint: {'center_x': 0.5, 'center_y': 0.1}

            Label:
                id: hrv_label
                text: "HRV  --  ms"
                color: get_color_from_hex('#e879f9')
                font_size: '16sp'
                size_hint_y: None
                height: dp(30)

            # Graph Area
            DarkCard:
                size_hint_y: None
                height: dp(120)
                padding: dp(10)
                FloatLayout:
                    id: graph_container

            # Stats Row
            BoxLayout:
                size_hint_y: None
                height: dp(60)
                spacing: dp(10)
                PillBox:
                    id: stat_rest
                    value: "65"
                    label: "RESTING"
                PillBox:
                    id: stat_hrv
                    value: "42"
                    label: "HRV (ms)"
                PillBox:
                    id: stat_status
                    value: "clear"
                    label: "STATUS"
                    color_val: get_color_from_hex('#4ade80')

            Widget:
                size_hint_y: 0.1

            SmoothButton:
                id: connect_btn
                text: 'disconnect'
                size_hint_y: None
                height: dp(55)
                background_color: get_color_from_hex('#1e1630')
                on_release: root.toggle_connection()

        # Sliding Alert Card
        FloatLayout:
            id: alert_card
            size_hint: 0.9, None
            height: dp(160)
            pos_hint: {'center_x': 0.5}
            y: -self.height - dp(20) # Hidden initially
            
            canvas.before:
                Color:
                    rgba: get_color_from_hex('#7c3aed') # Border
                RoundedRectangle:
                    pos: self.x - dp(2), self.y - dp(2)
                    size: self.width + dp(4), self.height + dp(4)
                    radius: [17]
                Color:
                    rgba: get_color_from_hex('#0d0b16') # Background
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
            
            BoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(10)
                
                Label:
                    id: alert_title
                    text: "spike detected"
                    color: get_color_from_hex('#e879f9')
                    font_size: '20sp'
                    bold: True
                    halign: 'left'
                    text_size: self.size
                    
                Label:
                    id: alert_desc
                    text: "Heart rate rose rapidly by 35 BPM."
                    color: get_color_from_hex('#6d5fa0')
                    font_size: '14sp'
                    halign: 'left'
                    valign: 'top'
                    text_size: self.size
                    
                SmoothButton:
                    text: 'ok - resting now'
                    height: dp(45)
                    size_hint_y: None
                    on_release: root.dismiss_alert()

<SettingsScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        
        FloatLayout:
            size_hint_y: None
            height: dp(50)
            GhostButton:
                text: '< back'
                pos_hint: {'x': 0, 'center_y': 0.5}
                size_hint: None, None
                size: dp(60), dp(40)
                on_release: root.manager.current = 'main'
            Label:
                text: 'profile'
                color: get_color_from_hex('#ede9fe')
                font_size: '22sp'
                bold: True
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                
        # Settings List
        ScrollView:
            BoxLayout:
                id: settings_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                # Populated in Python
                
        SmoothButton:
            text: 'back to monitor'
            size_hint_y: None
            height: dp(60)
            on_release: root.manager.current = 'main'

<DevPopupContent>:
    orientation: 'vertical'
    spacing: dp(15)
    padding: dp(10)
    TextInput:
        id: dev_code
        hint_text: 'Enter Developer Code'
        password: True
        multiline: False
        size_hint_y: None
        height: dp(50)
        background_color: get_color_from_hex('#1e1630')
        foreground_color: get_color_from_hex('#ede9fe')
    Label:
        id: dev_msg
        text: ''
        color: get_color_from_hex('#f43f5e')
        size_hint_y: None
        height: dp(20)
    SmoothButton:
        text: 'Unlock'
        size_hint_y: None
        height: dp(50)
        on_release: root.verify_code()
    Widget:
        size_hint_y: 1
'''

# --- CUSTOM WIDGETS & LOGIC ---

class DevPopupContent(BoxLayout):
    def __init__(self, popup_ref, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.popup_ref = popup_ref
        self.app = app_ref

    def verify_code(self):
        if self.ids.dev_code.text == "Ryan_5610":
            self.clear_widgets()
            lbl = Label(text="Simulator Scenarios", color=get_color_from_hex('#ede9fe'), size_hint_y=None, height=40)
            self.add_widget(lbl)
            
            scenarios = ['resting', 'walking', 'pots_spike', 'sustained', 'recovery']
            for sc in scenarios:
                btn = type('Btn', (App.get_running_app().factory_SmoothButton,), {})()
                btn.text = sc
                btn.size_hint_y = None
                btn.height = 45
                btn.bind(on_release=lambda x, s=sc: self.activate_scenario(s))
                self.add_widget(btn)
        else:
            self.ids.dev_code.text = ""
            self.ids.dev_msg.text = "wrong code — try again"

    def activate_scenario(self, scenario):
        self.app.main_screen.simulator_scenario = scenario
        self.popup_ref.dismiss()


class GraphWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = deque([0]*60, maxlen=60)
        with self.canvas:
            Color(rgba=get_color_from_hex('#7c3aed'))
            self.line = Line(points=[], width=1.5)
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def add_point(self, value):
        self.history.append(value)
        self.update_graphics()

    def update_graphics(self, *args):
        if not self.history:
            return
        
        x_step = self.width / 59 if self.width else 1
        min_val = min(self.history) - 10
        max_val = max(self.history) + 10
        val_range = max_val - min_val if max_val != min_val else 1

        points = []
        for i, val in enumerate(self.history):
            x = self.x + (i * x_step)
            y = self.y + ((val - min_val) / val_range) * self.height
            points.extend([x, y])
        
        self.line.points = points


class OnboardingNameScreen(Screen):
    def next_screen(self):
        name = self.ids.name_input.text.strip()
        if name:
            app = App.get_running_app()
            app.user_profile['name'] = name
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'onboard_rest'

class OnboardingRestingScreen(Screen):
    def next_screen(self):
        app = App.get_running_app()
        rest = int(self.ids.rest_slider.value)
        app.user_profile['resting_bpm'] = rest
        app.user_profile['alert_threshold'] = rest + 45
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'onboard_spike'

class OnboardingSpikeScreen(Screen):
    def finish_onboarding(self):
        app = App.get_running_app()
        app.user_profile['spike_delta'] = int(self.ids.spike_slider.value)
        app.save_profile()
        app.setup_main_screen()
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'main'


class MainMonitorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.graph = GraphWidget()
        Clock.schedule_once(self._add_graph, 0)
        
        self.tap_count = 0
        self.last_tap_time = 0
        
        self.simulator_scenario = 'resting'
        self.sim_tick = 0
        self.current_bpm = 65
        self.alert_active = False
        
        # Engine Logic State
        self.sustained_timer = 0
        
    def _add_graph(self, dt):
        self.ids.graph_container.add_widget(self.graph)

    def on_enter(self):
        app = App.get_running_app()
        name = app.user_profile.get('name', 'there')
        
        # Time-based greeting
        hour = datetime.now().hour
        if hour < 12:
            greet = f"good morning, {name}"
        elif hour < 18:
            greet = f"good afternoon, {name}"
        elif hour < 22:
            greet = f"good evening, {name}"
        else:
            greet = f"hey {name}, rest up"
            
        self.ids.greeting_label.text = greet
        self.ids.profile_initial.text = name[0].upper() if name else "?"
        
        self.ids.stat_rest.value = str(app.user_profile.get('resting_bpm', 65))
        
        # Start reading data (Simulator or BLE)
        Clock.schedule_interval(self.update_monitor, 1.0)

    def handle_profile_tap(self):
        current_time = time.time()
        if current_time - self.last_tap_time < 1.5:
            self.tap_count += 1
        else:
            self.tap_count = 1
            
        self.last_tap_time = current_time
        
        if self.tap_count == 1:
            Clock.schedule_once(self._go_to_settings, 0.4)
            
        if self.tap_count == 5:
            Clock.unschedule(self._go_to_settings)
            self.open_dev_mode()
            self.tap_count = 0

    def _go_to_settings(self, dt):
        if self.tap_count < 5:
            app = App.get_running_app()
            app.setup_settings_screen()
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'settings'

    def open_dev_mode(self):
        app = App.get_running_app()
        content = DevPopupContent(popup_ref=None, app_ref=app)
        popup = Popup(title='Developer Mode', content=content, size_hint=(0.8, 0.5),
                      background_color=get_color_from_hex('#1e1630'), title_color=get_color_from_hex('#e879f9'))
        content.popup_ref = popup
        popup.open()

    def toggle_connection(self):
        btn = self.ids.connect_btn
        if btn.text == 'disconnect':
            btn.text = 'connecting...'
            btn.background_color = get_color_from_hex('#6d5fa0')
            Clock.schedule_once(lambda dt: self._set_conn('connect to band'), 1)
            self.ids.status_label.text = "disconnected"
        else:
            btn.text = 'connecting...'
            Clock.schedule_once(lambda dt: self._set_conn('disconnect'), 1.5)
            self.ids.status_label.text = "connected — monitoring"
            
    def _set_conn(self, text):
        self.ids.connect_btn.text = text
        self.ids.connect_btn.background_color = get_color_from_hex('#1e1630') if text == 'disconnect' else get_color_from_hex('#7c3aed')

    def trigger_alert(self, title, desc):
        if self.alert_active: return
        self.alert_active = True
        
        self.ids.alert_title.text = title
        self.ids.alert_desc.text = desc
        
        card = self.ids.alert_card
        anim = Animation(y=dp(20), duration=0.35, transition='out_back')
        anim.start(card)
        
        self.ids.stat_status.value = "alert"
        self.ids.stat_status.color_val = get_color_from_hex('#f43f5e')

    def dismiss_alert(self):
        card = self.ids.alert_card
        anim = Animation(y=-card.height - dp(20), duration=0.25, transition='in_quad')
        anim.start(card)
        self.alert_active = False
        
        self.ids.stat_status.value = "recovering"
        self.ids.stat_status.color_val = get_color_from_hex('#e879f9')
        
        Clock.schedule_once(lambda dt: self._clear_status(), 10)

    def _clear_status(self):
        if not self.alert_active:
            self.ids.stat_status.value = "clear"
            self.ids.stat_status.color_val = get_color_from_hex('#4ade80')

    def update_monitor(self, dt):
        if self.ids.status_label.text == "disconnected":
            return
            
        app = App.get_running_app()
        resting = app.user_profile.get('resting_bpm', 65)
        spike_delta = app.user_profile.get('spike_delta', 30)
        threshold = app.user_profile.get('alert_threshold', 110)
        
        if USE_SIMULATOR:
            self.sim_tick += 1
            if self.simulator_scenario == 'resting':
                target = resting
            elif self.simulator_scenario == 'walking':
                target = 85
            elif self.simulator_scenario == 'pots_spike':
                target = resting + spike_delta + 15
                if self.sim_tick > 10: 
                    self.simulator_scenario = 'recovery'
                    self.sim_tick = 0
            elif self.simulator_scenario == 'sustained':
                target = threshold + 5
            elif self.simulator_scenario == 'recovery':
                target = resting + ((self.current_bpm - resting) * 0.9) 
                
            noise = random.uniform(-2, 2)
            self.current_bpm = int(target + noise)
            hrv = random.randint(35, 55)
        else:
            pass
            
        bpm_lbl = self.ids.bpm_label
        bpm_lbl.text = str(self.current_bpm)
        self.ids.hrv_label.text = f"HRV  {hrv}  ms"
        
        target_color = '#ede9fe' 
        if self.current_bpm >= threshold:
            target_color = '#f43f5e' 
        elif self.current_bpm >= resting + 15:
            target_color = '#e879f9' 
            
        current_hex = '#{:02x}{:02x}{:02x}'.format(*[int(c*255) for c in bpm_lbl.color[:3]])
        if current_hex != target_color:
            anim = Animation(color=get_color_from_hex(target_color), duration=0.5)
            anim.start(bpm_lbl)

        self.graph.add_point(self.current_bpm)
        
        if self.current_bpm >= resting + spike_delta:
            self.trigger_alert("spike detected", f"Heart rate rose rapidly by {self.current_bpm - resting} BPM from baseline.")
            
        if self.current_bpm >= threshold:
            self.sustained_timer += 1
            if self.sustained_timer >= 10:
                self.trigger_alert("sustained HR", f"Heart rate has been above {threshold} BPM for 10+ seconds.")
                self.sustained_timer = 0
        else:
            self.sustained_timer = 0


class SettingsScreen(Screen):
    pass


class PaceRingApp(App):
    user_profile = {}

    @property
    def profile_path(self):
        # This dynamically gets the safe Android storage path
        return os.path.join(self.user_data_dir, 'profile.json')

    def build(self):
        from kivy.factory import Factory
        self.factory_SmoothButton = Factory.SmoothButton
        
        Builder.load_string(KV)
        self.load_profile()
        
        self.sm = ScreenManager()
        
        if not self.user_profile:
            self.sm.add_widget(OnboardingNameScreen(name='onboard_name'))
            self.sm.add_widget(OnboardingRestingScreen(name='onboard_rest'))
            self.sm.add_widget(OnboardingSpikeScreen(name='onboard_spike'))
        
        self.main_screen = MainMonitorScreen(name='main')
        self.settings_screen = SettingsScreen(name='settings')
        
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.settings_screen)
        
        if self.user_profile:
            self.sm.current = 'main'
            
        return self.sm

    def load_profile(self):
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r') as f:
                    self.user_profile = json.load(f)
            except Exception:
                self.user_profile = {}

    def save_profile(self):
        with open(self.profile_path, 'w') as f:
            json.dump(self.user_profile, f)

    def setup_main_screen(self):
        self.main_screen.on_enter()

    def setup_settings_screen(self):
        settings_box = self.settings_screen.ids.settings_list
        settings_box.clear_widgets()
        
        config_map = {
            'Name': self.user_profile.get('name', ''),
            'Resting BPM': str(self.user_profile.get('resting_bpm', 65)),
            'Alert Threshold': str(self.user_profile.get('alert_threshold', 110)),
            'Spike Delta': '+' + str(self.user_profile.get('spike_delta', 30)),
            'Vibration': 'On',
            'Sound Alerts': 'On'
        }
        
        for key, val in config_map.items():
            row = FloatLayout(size_hint_y=None, height=50)
            
            with row.canvas.before:
                Color(rgba=get_color_from_hex('#0d0b16'))
                from kivy.graphics import RoundedRectangle
                row.bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[10])
            row.bind(pos=self._update_rect, size=self._update_rect)
                
            lbl_key = Label(text=key, color=get_color_from_hex('#6d5fa0'), halign='left', pos_hint={'x': 0.05, 'center_y': 0.5})
            lbl_key.bind(size=lbl_key.setter('text_size'))
            
            lbl_val = Label(text=val, color=get_color_from_hex('#ede9fe'), bold=True, halign='right', pos_hint={'right': 0.95, 'center_y': 0.5})
            lbl_val.bind(size=lbl_val.setter('text_size'))
            
            row.add_widget(lbl_key)
            row.add_widget(lbl_val)
            settings_box.add_widget(row)

    def _update_rect(self, instance, value):
        instance.bg.pos = instance.pos
        instance.bg.size = instance.size

def dp(val):
    from kivy.metrics import dp as dp_func
    return dp_func(val)

if __name__ == '__main__':
    PaceRingApp().run()
