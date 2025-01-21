import psutil
import os
import sys
from PyQt5.QtCore import Qt, QTimerEvent
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QHBoxLayout,
)
from multiprocessing import Process
from PyQt5.QtGui import QPixmap, QCursor
from settings import SettingsWindow  # Import the settings window class
from data_wifi_control import DataUsageTracker # Import the data usage tracker class

class RealTimeInternetUsageMonitor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time Internet Usage Monitor")
        self.setGeometry(100, 100, 400, 100)
        
        # Store the initial baseline network stats
        self.initial_data_sent = psutil.net_io_counters().bytes_sent
        self.initial_data_received = psutil.net_io_counters().bytes_recv
        self.total_data_used = 0.0  # Initialize total data used to 0
        

        layout = QVBoxLayout(self)

        self.data_usage_label = QLabel("Data Usage: 0 MB")
        layout.addWidget(self.data_usage_label)

        '''always_on_top_checkbox = QCheckBox("Always on top")
        layout.addWidget(always_on_top_checkbox)

        always_on_top_checkbox.setChecked(False)
        always_on_top_checkbox.stateChanged.connect(self.handle_always_on_top)'''
        
        # Bottom layout
        bottom_layout = QHBoxLayout()
        
        always_on_top_checkbox = QCheckBox("Always on top")
        #main_layout.addWidget(always_on_top_checkbox)

        always_on_top_checkbox.setChecked(False)
        always_on_top_checkbox.stateChanged.connect(self.handle_always_on_top)
        
        bottom_layout.addWidget(always_on_top_checkbox)

        # Spacer to push the settings icon to the bottom-right
        bottom_layout.addStretch()
        
        # Settings Icon (Bottom-Right)
        settings_icon = QLabel(self)
        settings_icon.setPixmap(QPixmap("images/settings.png").scaled(40, 40, Qt.KeepAspectRatio))
        settings_icon.setCursor(QCursor(Qt.PointingHandCursor))
        settings_icon.mousePressEvent = self.open_settings  # Connect click to settings window
        bottom_layout.addWidget(settings_icon)

        # Add the bottom layout to the main layout
        layout.addLayout(bottom_layout)

        self.startTimer(100)
        self.show()
        
        self.update_data_usage = 0.0
        # Data Wifi Control
        if os.path.exists("settings_data.json"):
            # Initialize data tracking
            '''self.data_tracker = DataUsageTracker(self)
            self.data_tracker.exec_()
            self.data_tracker.start_tracking()
            # Start the data tracker as a separate process
            data_tracker_process = Process(target=self.start_data_tracker)
            data_tracker_process.start()'''
            self.start_data_tracker()
    

    def timerEvent(self, event: QTimerEvent):
        # Use psutil to monitor network usage
        network_stats = psutil.net_io_counters()
        data_sent = network_stats.bytes_sent
        data_received = network_stats.bytes_recv

        # Calculate total data usage since program start
        self.total_data_used = (data_sent - self.initial_data_sent) + (data_received - self.initial_data_received)
        
        # Calculate total data usage in MB
        total_data_mb = self.total_data_used / (1024**2)

        # Update the label in the main thread
        self.update_label(total_data_mb)

    def update_label(self, data_usage_mb: float):
        # Update the label with the new data usage
        self.data_usage_label.setText(f"Data Usage: {data_usage_mb:.2f} MB")

    def handle_always_on_top(self, toggled: bool):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, toggled)
        self.show()
        
    def open_settings(self, event):
        # Open the Settings Window
        settings_window = SettingsWindow(self)
        settings_window.exec_()
        
    '''def data_wifi_control(self):
        # Open data wifi control window
        #if os.path.exists("settings_data.json"):
        data_wifi_control = DataUsageTracker(self)
        data_wifi_control.exec_()'''
        
    def start_data_tracker(self):
        os.system("python data_wifi_control.py")
        
    def start_data_tracker(self):
        """Start the data tracker program as an external script."""
        try:
            # Use subprocess to run the external script
            self.data_tracker_process = subprocess.Popen(
                [sys.executable, "data_wifi_control.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"Failed to start data tracker: {e}")
            
    def closeEvent(self, event):
        """Ensure the data tracker process is terminated when the main window is closed."""
        if self.data_tracker_process:
            self.data_tracker_process.terminate()
        super().closeEvent(event)


class App(QApplication):
    def __init__(self):
        super().__init__([])
        self.window = RealTimeInternetUsageMonitor()


app = App()
app.exec()
