import os
import psutil
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal

class DataUsageTracker(QThread):
    # Signals for GUI updates
    wifi_disabled = pyqtSignal()
    data_limit_alert = pyqtSignal()
    exceeded_data_limit_alert = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.data_limit = None  # in bytes
        self.exceeded_data_limit = None  # in bytes or None for unlimited
        self.enable_data_limit = False
        self.enable_alert_message = False
        self.total_data_used = 0  # in bytes
        self.adapter_name = self.get_wifi_adapter()
        self.running = True

    def load_settings(self):
        """Load settings from files."""
        if os.path.exists('data-limit.json'):
            with open('data-limit.json', 'r') as file:
                self.data_limit = int(file.read())
        
        if os.path.exists('exceeded-data-limit.json'):
            with open('exceeded-data-limit.json', 'r') as file:
                exceeded_data = file.read()
                if exceeded_data == 'unlimited':
                    self.exceeded_data_limit = None
                else:
                    self.exceeded_data_limit = int(exceeded_data)

        # Default enable states can be hardcoded or loaded from other files

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

    def disable_wifi(self):
        """Disable the Wi-Fi adapter."""
        os.system(f'netsh interface set interface "{self.adapter_name}" admin=disable')
        self.wifi_disabled.emit()

    def run(self):
        """Start tracking data usage."""
        self.load_settings()
        initial_data_usage = self.get_data_usage()

        while self.running:
            current_data_usage = self.get_data_usage()
            self.total_data_used = current_data_usage - initial_data_usage

            if self.enable_data_limit and self.data_limit and self.total_data_used >= self.data_limit:
                if self.enable_alert_message:
                    self.data_limit_alert.emit()
                else:
                    self.disable_wifi()

            if self.exceeded_data_limit is not None and self.total_data_used >= self.exceeded_data_limit:
                self.exceeded_data_limit_alert.emit()
                self.disable_wifi()

            time.sleep(1)  # Check every second

class DataUsageApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.tracker = DataUsageTracker()
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
        response = QMessageBox.question(
            self, "Data Limit Reached",
            "You have reached your data limit. Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if response == QMessageBox.No:
            self.tracker.disable_wifi()

    def show_exceeded_data_limit_alert(self):
        QMessageBox.warning(self, "Exceeded Data Limit", "You have exceeded your data limit. Wi-Fi will be disabled.")

    def closeEvent(self, event):
        self.tracker.running = False
        self.tracker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication([])
    window = DataUsageApp()
    window.show()
    app.exec_()
