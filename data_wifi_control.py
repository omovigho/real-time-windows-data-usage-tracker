import os
import psutil
import time
import json
import pywifi
import sys

from PyQt5.QtCore import Qt, QTimerEvent
from pywifi import const
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMessageBox
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QHBoxLayout,
)
from PyQt5.QtCore import QThread, pyqtSignal

class DataUsageTracker(QThread):
    # Signals for GUI updates
    wifi_disabled = pyqtSignal()
    data_limit_alert = pyqtSignal()
    exceeded_data_limit_alert = pyqtSignal()
    data_usage_updated = pyqtSignal(float)

    def __init__(self, enable_exceeded_limit=False):
        super().__init__()
        
        # Store the initial baseline network stats
        self.initial_data_sent = psutil.net_io_counters().bytes_sent
        self.initial_data_received = psutil.net_io_counters().bytes_recv
        self.total_data_used = 0.0  # Initialize total data used to 0
        print("Tracking already.. --")
        self.data_limit = None  # in bytes
        #self.total_data_used = 0  # in bytes
        self.total_exceeded_data = 0.0
        self.check_data_limit = False  # preventing data enable-alert-message popping up multiple times
        self.exceeded_data_limit = enable_exceeded_limit
        self.adapter_name = self.get_wifi_adapter()
        self.settings_data = self.load_settings()
        self.running = True
        print(f'settings are: {self.settings_data['data-limit']}')
        print(f'running is {self.running}')
        self.startTimer(100)
        #self.run()
        #self.show()
        

    def load_settings(self):
        try:
            with open("settings_data.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

        # Default enable states can be hardcoded or loaded from other files
        
    def disconnect_wifi(self):
        wifi = pywifi.PyWiFi()
        iface = wifi.interfaces()[0]
        iface.disconnect()
        time.sleep(1)
        if iface.status() == const.IFACE_DISCONNECTED:
            print("Wi-Fi disconnected successfully.")
            self.exit_program()
        else:
            print("Failed to disconnect Wi-Fi.")

    '''def get_wifi_adapter(self):
        """Get the name of the Wi-Fi adapter."""
        for adapter, stats in psutil.net_if_stats().items():
            if "wi-fi" in adapter.lower() or "wireless" in adapter.lower():
                return adapter
        return None'''

    def get_data_usage(self):
        """Get total data usage for the Wi-Fi adapter."""
        if self.adapter_name and self.adapter_name in psutil.net_io_counters(pernic=True):
            stats = psutil.net_io_counters(pernic=True)[self.adapter_name]
            return stats.bytes_sent + stats.bytes_recv
        return 0
        
    def timerEvent(self, event: QTimerEvent):
        # Use psutil to monitor network usage
        network_stats = psutil.net_io_counters()
        data_sent = network_stats.bytes_sent
        data_received = network_stats.bytes_recv

        # Calculate total data usage since program start
        self.total_data_used = (data_sent - self.initial_data_sent) + (data_received - self.initial_data_received)

        # Convert to MB for display
        '''total_data_in_mb = self.total_data_used / (1024 ** 2)
        print(f"Total data used: {total_data_in_mb:.2f} MB")'''

        
        
    

    ''def disable_wifi(self):
        """Disable the Wi-Fi adapter."""
        os.system(f'netsh interface set interface "{self.adapter_name}" admin=disable')
        self.wifi_disabled.emit()''

    def run(self):
        """Start tracking data usage."""
        while self.running:
            #current_data_usage = self.get_data_usage()
            #self.total_data_used = current_data_usage - initial_data_usage
            #print("The program is running.. --")

            #if self.enable_data_limit and self.data_limit and self.total_data_used >= self.data_limit:
            if self.settings_data['enable-data-limit'] == True and self.settings_data['data-limit'] != 'Null':
                if self.total_data_used >= self.settings_data['data-limit']:
                    if self.check_data_limit == False:
                        if self.settings_data['enable-alert-message'] == True:
                            self.data_limit_alert.emit()
                            self.check_data_limit = True
                        else:
                            self.wifi_disabled.emit()
                            time.sleep(3)
                            self.disconnect_wifi()
                            self.running = False
                            

                if self.exceeded_data_limit == True:
                    
                    print(f'exceeded settings for are: {self.settings_data['exceeded-data-limit']}')
                    if self.settings_data['exceeded-data-limit'] == "Unlimited":
                        # Stop tracking when exceeded limit is unlimited
                        self.exit_program()
                        #self.running = False
                        
                    elif isinstance(self.settings_data['exceeded-data-limit'], (int, float)) == True:
                        #resetting data limit to the sum of data-limit and exceeded-data-limit 
                        self.total_exceeded_data = self.settings_data['data-limit'] + self.settings_data['exceeded-data-limit']   
                        if self.total_data_used >= self.total_exceeded_data:
                            self.exceeded_data_limit_alert.emit()
                            self.running = False
                            self.disconnect_wifi()

            time.sleep(1)  # Check every second
            
    def stop(self):
        self.running = False
        
    def exit_program(self):
        """Exit the entire program."""
        # Terminate the subprocess if running
        '''if self.data_tracker_process and self.data_tracker_process.poll() is None:
            self.data_tracker_process.terminate()'''

        # Exit the application
        QApplication.quit()

        # Terminate Python interpreter
        sys.exit()
    
    
class DataUsageApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.enable_exceeded_limit = False  # Define the variable with a default value
        
        self.tracker = DataUsageTracker(self.enable_exceeded_limit)
        self.tracker.wifi_disabled.connect(self.show_wifi_disabled_message)
        self.tracker.data_limit_alert.connect(self.show_data_limit_alert)
        self.tracker.exceeded_data_limit_alert.connect(self.show_exceeded_data_limit_alert)
        self.tracker.start()
        
        

    def init_ui(self):
        self.setWindowTitle("Data Usage Tracker")
        self.setGeometry(300, 300, 400, 200)
        

    def show_wifi_disabled_message(self):
        QMessageBox.critical(self, "Wi-Fi Disabled", "Your Wi-Fi has been disabled because you exceeded your data limit.")

    def show_data_limit_alert(self):
        """Show a confirmation dialog for data limit reached and handle user response."""
        if hasattr(self, "alert_in_progress") and self.alert_in_progress:
            # Prevent multiple dialogs
            return

        self.alert_in_progress = True  # Set flag to indicate an alert is in progress

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Data Limit Reached")
        msg_box.setText("You have reached your data limit. Do you want to use the exceeded data limit?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        response = msg_box.exec_()  # Show modal dialog and wait for user response

        if response == QMessageBox.Yes:
            self.enable_exceeded_limit = True
            self.tracker.exceeded_data_limit = self.enable_exceeded_limit  # Pass the value to the 
        else:
            self.tracker.disconnect_wifi()  # Disconnect WiFi

        self.alert_in_progress = False  # Reset flag after handling response


    def show_exceeded_data_limit_alert(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Exceeded Data Limit Reached")
        msg_box.setText("You have exceeded your data limit.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        #self.disconnect_wifi()
        #self.tracker.running = False
        #self.tracker.exit_program()
        
    '''def closeEvent(self, event):
        self.tracker.running = False
        self.tracker.wait()
        event.accept()
        
    def close_tracker(self):
        self.tracker.stop()
        self.close()'''

if __name__ == "__main__":
    app = QApplication([])
    window = DataUsageApp()
    window.show()
    app.exec_()
