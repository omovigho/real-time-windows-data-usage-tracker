from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import psutil
from scapy.all import sniff, IP
from scapy.layers.inet import IP
from scapy.all import ifaces
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from collections import defaultdict
import psutil
import win32gui
import win32ui
from datetime import datetime
import time
from settings import SettingsWindow  # Import the settings window class
from PyQt5.QtGui import QPixmap, QCursor

class SniffingThread(QThread):
    update = pyqtSignal()

    def __init__(self, process_packet, parent=None):
        super().__init__(parent)
        self.process_packet = process_packet

    def run(self):
        sniff(prn=self.process_packet, store=False, count=0)
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
            time.sleep(1)  # Adjusted interval for better efficiency
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
    all_macs = {iface.mac for iface in ifaces.values()}

    def __init__(self):
        super().__init__()
        self.is_program_running = True
        self.connection2pid = {}
        self.pid2traffic = defaultdict(lambda: [0, 0])

        self.setWindowTitle("App Data Tracker")
        self.setGeometry(100, 100, 300, 400)

        main_layout = QVBoxLayout(self)
        
        self.total_data_usage_label = QLabel("Total data usage: 0B")
        self.total_data_usage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.total_data_usage_label)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        widget = QWidget()
        
        self.lay = QVBoxLayout(widget)
        self.lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(widget)
        main_layout.addWidget(scroll_area)
        
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
        main_layout.addLayout(bottom_layout)

        self.listItems: dict[str, ExeDataWidget] = {}

        self.startTimer(1000)  # Adjusted to update every second

        self.start_monitoring()

    def get_executable_path(self, process_name):
        try:
            for proc in psutil.process_iter(attrs=["name", "exe"]):
                if proc.info["name"] == process_name:
                    return proc.info["exe"]
        except psutil.NoSuchProcess:
            pass
        return None

    def timerEvent(self, _):
        process_data = self.print_pid2traffic()
        total_upload = 0
        total_download = 0

        for process in process_data:
            executable_path = self.get_executable_path(process["name"])
            try:
                icons = win32gui.ExtractIconEx(executable_path, 0)
                icon = icons[0][0]
                width = height = 32
                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, width, height)
                hdc = hdc.CreateCompatibleDC()
                hdc.SelectObject(hbmp)
                win32gui.DrawIconEx(hdc.GetHandleOutput(), 0, 0, icon, width, height, 0, None, 0x0003)
                
                for iconList in icons:
                    for icon in iconList:
                        win32gui.DestroyIcon(icon)
                hdc.DeleteDC()
                win32gui.ReleaseDC(0, win32gui.GetDC(0))
                
                bitmapbits = hbmp.GetBitmapBits(True)
                image = QImage(bitmapbits, width, height, QImage.Format_ARGB32_Premultiplied)
                buffer = QBuffer()
                buffer.setOpenMode(QIODevice.ReadWrite)
                image.save(buffer, "PNG")
                image.loadFromData(buffer.data(), "PNG")
                pixmap = QPixmap.fromImage(image)
            except Exception:
                pixmap = QPixmap("default-icon.png")
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(32, 32)
            
            process_name = process["name"]
            total_data_usage = process["Upload"] + process["Download"]
            data_usage = process["Data Usage"] if total_data_usage == 0 else total_data_usage
            total_upload += process["Upload"]
            total_download += process["Download"]
            pid = process["pid"]
            item = self.listItems.get(pid)
            if not item:
                item = ExeDataWidget(self.lay, pixmap, process_name)
                self.listItems[pid] = item
            item.setValue(data_usage)
        
        total = total_download + total_upload
        self.total_data_usage_label.setText(f"Total data usage: {ExeDataWidget.get_size(None, total)}")
        
        for item in self.listItems.values():
            item.setMaximum(total)

    def _process_packet(self, packet):
        try:
            if IP in packet:
                ip_layer = packet[IP]
                packet_connection = (ip_layer.sport, ip_layer.dport)
                packet_pid = self.connection2pid.get(packet_connection)
                if packet_pid:
                    if packet.src in self.all_macs:
                        self.pid2traffic[packet_pid][0] += len(packet)
                    else:
                        self.pid2traffic[packet_pid][1] += len(packet)
        except AttributeError:
            pass

    def print_pid2traffic(self):
        processes = []
        for pid, traffic in self.pid2traffic.items():
            try:
                p = psutil.Process(pid)
                name = p.name()
                try:
                    create_time = datetime.fromtimestamp(p.create_time())
                except OSError:
                    create_time = datetime.fromtimestamp(psutil.boot_time())
                process = {
                    "pid": pid,
                    "name": name,
                    "create_time": create_time,
                    "Upload": traffic[0],
                    "Download": traffic[1],
                    "Data Usage": traffic[0] + traffic[1],
                }
                try:
                    process["Upload Speed"] = traffic[0] - self.global_df.at[pid, "Upload"]
                    process["Download Speed"] = traffic[1] - self.global_df.at[pid, "Download"]
                except (KeyError, AttributeError):
                    process["Upload Speed"] = traffic[0]
                    process["Download Speed"] = traffic[1]
                    process["Data Usage"] = traffic[0] + traffic[1]
                processes.append(process)
            except psutil.NoSuchProcess:
                continue
        return processes

    def start_monitoring(self):
        self.is_program_running = True
        self.connection_thread = ConnectionThread(self.connection2pid, self.is_program_running)
        self.sniffing_thread = SniffingThread(self._process_packet)
        
        self.connection_thread.update.connect(self.update_ui)
        self.sniffing_thread.update.connect(self.update_ui)
        
        self.connection_thread.start()
        self.sniffing_thread.start()

    def update_ui(self):
        self.timerEvent(None)

    def handle_always_on_top(self, toggled: bool):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, toggled)
        self.show()

    def closeEvent(self, _):
        self.is_program_running = False
        QApplication.instance().quit()
        

    def open_settings(self, event):
        # Open the Settings Window
        settings_window = SettingsWindow(self)
        settings_window.exec_()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ex = NetworkUsageGUI()
    ex.show()
    sys.exit(app.exec())
