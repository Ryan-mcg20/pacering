import threading
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.utils import platform

class POTSMonitor(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical')
        self.label = Label(text="POTS Monitor Initializing...", font_size='20sp')
        self.root.add_widget(self.label)
        
        # This prevents the "Loading... Crash" by starting the app BEFORE the heavy stuff
        Clock.schedule_once(self.check_permissions, 1)
        return self.root

    def check_permissions(self, dt):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.BLUETOOTH_CONNECT,
                    Permission.BLUETOOTH_SCAN,
                    Permission.ACCESS_FINE_LOCATION
                ], self.on_permissions_result)
                self.label.text = "Please allow permissions on your phone..."
            except Exception as e:
                self.label.text = f"Permission Error: {str(e)}"
        else:
            self.label.text = "Running on Desktop - No Bluetooth available"

    def on_permissions_result(self, permissions, grants):
        if all(grants):
            self.label.text = "Permissions Granted!\nReady to connect to Band."
            # Here is where we would start the BLE thread later
        else:
            self.label.text = "Permissions Denied.\nApp cannot function without Bluetooth."

if __name__ == "__main__":
    POTSMonitor().run()
