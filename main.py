import sys
import psutil
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtCore import Qt

class RealTimeInternetUsageMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Real-Time Internet Usage Monitor")
        self.setGeometry(100, 100, 400, 100)

        self.data_usage_label = QLabel("Data Usage: 0 MB")
        self.always_on_top_checkbox = QCheckBox("Always on top")
        self.always_on_top_checkbox.setChecked(False)
        self.always_on_top_checkbox.stateChanged.connect(self.handle_always_on_top)

        layout = QVBoxLayout()
        layout.addWidget(self.data_usage_label)
        layout.addWidget(self.always_on_top_checkbox)
        
        self.setLayout(layout)

        # Start a separate thread to monitor data usage
        self.monitor_thread = threading.Thread(target=self.monitor_data_usage)
        self.monitor_thread.daemon = True  # Allow the thread to exit when the main program exits
        self.monitor_thread.start()

    def handle_always_on_top(self, state):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, state)
        self.show()
        
    def monitor_data_usage(self):
        while True:
            # Use psutil to monitor network usage
            network_stats = psutil.net_io_counters()
            data_sent = network_stats.bytes_sent
            data_received = network_stats.bytes_recv

            # Calculate total data usage in MB
            total_data_mb = (data_sent + data_received) / (1024 * 1024)

            # Update the label in the main thread
            self.update_label(total_data_mb)

    def update_label(self, data_usage_mb):
        # Update the label with the new data usage
        self.data_usage_label.setText(f"Data Usage: {data_usage_mb:.2f} MB")

def main():
    app = QApplication(sys.argv)
    window = RealTimeInternetUsageMonitor()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
