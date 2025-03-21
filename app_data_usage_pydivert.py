from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import psutil
import pydivert
from collections import defaultdict
import win32gui
import win32ui
from datetime import datetime
import time
from settings import SettingsWindow  # Import the settings window class

class SniffingThread(QThread):
    update = pyqtSignal()

    def __init__(self, process_packet, parent=None):
        super().__init__(parent)
        self.process_packet = process_packet

    def run(self):
        with pydivert.WinDivert("inbound or outbound") as w:
            for packet in w:
                self.process_packet(packet)
                w.send(packet)
        self.update.emit()

class ConnectionThread(QThread):
    update = pyqtSignal()

    def __init__(self, connection2pid, is_program_running, parent=None):
        super().__init__(parent)
        self.connection2pid = connection2pid
        self.is_program_running = is_program_running

    def run(self):
        while self.is_program_running:
            for c in psutil.net_connections():
                if c.laddr and c.raddr and c.pid:
                    self.connection2pid[(c.laddr.port, c.raddr.port)] = c.pid
                    self.connection2pid[(c.raddr.port, c.laddr.port)] = c.pid
            time.sleep(1)
        self.update.emit()

class ExeDataWidget(QWidget):
    def get_size(self, bytes: int) -> str:
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < 1024:
                return f"{bytes:.2f}{unit}B"
            bytes /= 1024

    def __init__(self, lay: QVBoxLayout, pixmap: QPixmap, name: str):
        super().__init__()
        self.value = 0
        hlay = QHBoxLayout(self)
        self.pixmap = QLabel()
        self.pixmap.setPixmap(pixmap)
        self.pixmap.setFixedSize(32, 32)
        hlay.addWidget(self.pixmap)
        vlay = QVBoxLayout()
        hlay.addLayout(vlay)
        hlay2 = QHBoxLayout()
        vlay.addLayout(hlay2)
        self.name = QLabel(name)
        hlay2.addWidget(self.name)
        hlay2.addStretch()
        self.data_usage = QLabel()
        hlay2.addWidget(self.data_usage)
        self.progress = QProgressBar()
        vlay.addWidget(self.progress)
        lay.addWidget(self)

    def setValue(self, value: int):
        self.data_usage.setText(self.get_size(value))
        self.progress.setValue(value)

    def setMaximum(self, maximum: int):
        self.progress.setMaximum(maximum)

class NetworkUsageGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.is_program_running = True
        self.connection2pid = {}
        self.pid2traffic = defaultdict(lambda: [0, 0])
        self.setWindowTitle("App Data Tracker")
        self.setGeometry(100, 100, 300, 400)
        main_layout = QVBoxLayout(self)
        self.total_data_usage_label = QLabel("Total data usage: 0B")
        self.total_data_usage_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.total_data_usage_label)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        self.lay = QVBoxLayout(widget)
        self.lay.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(widget)
        main_layout.addWidget(scroll_area)
        bottom_layout = QHBoxLayout()
        always_on_top_checkbox = QCheckBox("Always on top")
        always_on_top_checkbox.setChecked(False)
        always_on_top_checkbox.stateChanged.connect(self.handle_always_on_top)
        bottom_layout.addWidget(always_on_top_checkbox)
        bottom_layout.addStretch()
        settings_icon = QLabel(self)
        settings_icon.setPixmap(QPixmap("images/settings.png").scaled(40, 40, Qt.KeepAspectRatio))
        settings_icon.setCursor(QCursor(Qt.PointingHandCursor))
        settings_icon.mousePressEvent = self.open_settings
        bottom_layout.addWidget(settings_icon)
        main_layout.addLayout(bottom_layout)
        self.listItems = {}
        self.startTimer(1000)
        self.start_monitoring()

    def timerEvent(self, _):
        process_data = self.print_pid2traffic()
        total_upload = 0
        total_download = 0
        for process in process_data:
            process_name = process["name"]
            total_data_usage = process["Upload"] + process["Download"]
            total_upload += process["Upload"]
            total_download += process["Download"]
            pid = process["pid"]
            item = self.listItems.get(pid)
            if not item:
                item = ExeDataWidget(self.lay, QPixmap("default-icon.png"), process_name)
                self.listItems[pid] = item
            item.setValue(total_data_usage)
        total = total_download + total_upload
        self.total_data_usage_label.setText(f"Total data usage: {ExeDataWidget.get_size(None, total)}")
        for item in self.listItems.values():
            item.setMaximum(total)

    def _process_packet(self, packet):
        try:
            packet_pid = self.connection2pid.get((packet.src_port, packet.dst_port))
            if packet_pid:
                if packet.is_outbound:
                    self.pid2traffic[packet_pid][0] += len(packet.raw)
                else:
                    self.pid2traffic[packet_pid][1] += len(packet.raw)
        except AttributeError:
            pass

    def print_pid2traffic(self):
        processes = []
        for pid, traffic in self.pid2traffic.items():
            try:
                p = psutil.Process(pid)
                processes.append({
                    "pid": pid,
                    "name": p.name(),
                    "Upload": traffic[0],
                    "Download": traffic[1],
                })
            except psutil.NoSuchProcess:
                continue
        return processes

    def start_monitoring(self):
        self.is_program_running = True
        self.connection_thread = ConnectionThread(self.connection2pid, self.is_program_running)
        self.sniffing_thread = SniffingThread(self._process_packet)
        self.connection_thread.start()
        self.sniffing_thread.start()

    def handle_always_on_top(self, toggled):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, toggled)
        self.show()

    def closeEvent(self, _):
        self.is_program_running = False
        QApplication.instance().quit()

    def open_settings(self, event):
        settings_window = SettingsWindow(self)
        settings_window.exec_()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = NetworkUsageGUI()
    window.show()
    sys.exit(app.exec())
