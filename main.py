import psutil
from PyQt5.QtCore import Qt, QTimerEvent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QCheckBox,
)


class RealTimeInternetUsageMonitor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time Internet Usage Monitor")
        self.setGeometry(100, 100, 400, 100)

        layout = QVBoxLayout(self)

        self.data_usage_label = QLabel("Data Usage: 0 MB")
        layout.addWidget(self.data_usage_label)

        always_on_top_checkbox = QCheckBox("Always on top")
        layout.addWidget(always_on_top_checkbox)

        always_on_top_checkbox.setChecked(False)
        always_on_top_checkbox.stateChanged.connect(self.handle_always_on_top)

        self.startTimer(100)
        self.show()

    def timerEvent(self, event: QTimerEvent):
        # Use psutil to monitor network usage
        network_stats = psutil.net_io_counters()
        data_sent = network_stats.bytes_sent
        data_received = network_stats.bytes_recv

        # Calculate total data usage in MB
        total_data_mb = (data_sent + data_received) / (1024**2)

        # Update the label in the main thread
        self.update_label(total_data_mb)

    def update_label(self, data_usage_mb: float):
        # Update the label with the new data usage
        self.data_usage_label.setText(f"Data Usage: {data_usage_mb:.2f} MB")

    def handle_always_on_top(self, toggled: bool):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, toggled)
        self.show()


class App(QApplication):
    def __init__(self):
        super().__init__([])
        self.window = RealTimeInternetUsageMonitor()


app = App()
app.exec()
