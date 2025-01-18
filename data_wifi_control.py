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
from PyQt5.QtCore import QThread, pyqtSignal

class DataUsageTracker(QThread):
    # Signals for GUI updates
    wifi_disabled = pyqtSignal()
    data_limit_alert = pyqtSignal()
    exceeded_data_limit_alert = pyqtSignal()

    def __init__(self, enable_exceeded_limit):
        super().__init__()
        self.data_limit = None  # in bytes
        self.total_data_used = 0  # in bytes
        self.exceeded_data_limit = enable_exceeded_limit
        self.adapter_name = self.get_wifi_adapter()
        self.settings_data = self.load_settings()
        self.running = True
        self.startTimer(100)
        #self.show()
        self.total_data_used = 0.00

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

    def get_wifi_adapter(self):
        """Get the name of the Wi-Fi adapter."""
        for adapter, stats in psutil.net_if_stats().items():
            if "wi-fi" in adapter.lower() or "wireless" in adapter.lower():
                return adapter
        return None

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

        # Calculate total data usage in MB
        self.total_data_used = (data_sent + data_received)

        # Update the label in the main thread
        #self.update_label(total_data_mb)

    def disable_wifi(self):
        """Disable the Wi-Fi adapter."""
        os.system(f'netsh interface set interface "{self.adapter_name}" admin=disable')
        self.wifi_disabled.emit()

    def run(self):
        """Start tracking data usage."""
        #self.load_settings()
        initial_data_usage = self.get_data_usage()

        while self.running:
            #current_data_usage = self.get_data_usage()
            #self.total_data_used = current_data_usage - initial_data_usage

            #if self.enable_data_limit and self.data_limit and self.total_data_used >= self.data_limit:
            if self.settings_data['enable-data-limit'] == True and self.settings_data['data-limit'] != 'Null':
                if self.total_data_used >= self.settings_data['data-limit']:
                    if self.settings_data['enable-alert-message'] == True:
                        self.data_limit_alert.emit()
                    else:
                        self.disconnect_wifi()
                        self.running = False

            if self.exceeded_data_limit == True:
                if self.settings_data['exceeded-data-limit'] == "Unlimited":
                    # Stop tracking when exceeded limit is unlimited
                    self.running = False
                    self.exit_program()
                elif self.total_data_used >= (self.settings_data['data-limit'] + self.settings_data['exceeded-data-limit']):
                    self.exceeded_limit_reached.emit()
                    self.running = False
                    self.exit_program()

            time.sleep(1)  # Check every second
            
    def stop(self):
        self.running = False
        
    def exit_program(self):
        """Close the window and exit the program."""
        self.close()  # Close the main window
        QApplication.instance().quit()  # Exit the QApplication
        sys.exit(0)  # Ensure the Python process terminates
    
    
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
            self.tracker.exceeded_data_limit = self.enable_exceeded_limit  # Pass the value to the tracker
        else:
            self.tracker.disconnect_wifi()  # Disconnect WiFi
            #self.tracker.stop()            # Stop the tracker

        self.alert_in_progress = False  # Reset flag after handling response


    def show_exceeded_data_limit_alert(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Exceeded Data Limit Reached")
        msg_box.setText("You have exceeded your data limit.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        self.disconnect_wifi()
        #self.tracker.running = False
        #self.tracker.exit_program()
        
    def closeEvent(self, event):
        self.tracker.running = False
        self.tracker.wait()
        event.accept()
        
    def close_tracker(self):
        self.tracker.stop()
        self.close()

if __name__ == "__main__":
    app = QApplication([])
    window = DataUsageApp()
    window.show()
    app.exec_()
