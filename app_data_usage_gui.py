from scapy.all import *
import psutil
#import win32com.client
import win32ui, win32gui, shutil
from collections import defaultdict
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QBuffer, QIODevice

from PyQt5.QtWidgets import *


class NetworkUsageGUI(QWidget):

    # get the all network adapter's MAC addresses
    all_macs = {iface.mac for iface in ifaces.values()}
    # A dictionary to map each connection to its correponding process ID (PID)
    connection2pid = {}
    # A dictionary to map each process ID (PID) to total Upload (0) and Download (1) traffic
    pid2traffic = defaultdict(lambda: [0, 0])
    # the global Pandas DataFrame that's used to track previous traffic stats
    global_df = None
    # global boolean for status of the program
    is_program_running = True

    def get_size(self, bytes: int) -> str:
        """
        Returns size of bytes in a nice format
        """
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < 1024:
                return f"{bytes:.2f}{unit}B"
            bytes /= 1024

    def _process_packet(self, packet):
        try:
            # get the packet source & destination IP addresses and ports
            packet_connection = (packet.sport, packet.dport)
            # get the PID responsible for this connection from our `connection2pid` global dictionary
            packet_pid = self.connection2pid.get(packet_connection)
            if packet_pid:
                if packet.src in self.all_macs:
                    # the source MAC address of the packet is our MAC address
                    # so it's an outgoing packet, meaning it's upload
                    self.pid2traffic[packet_pid][0] += len(packet)
                else:
                    # incoming packet, download
                    self.pid2traffic[packet_pid][1] += len(packet)
        except (AttributeError, IndexError):
            # sometimes the packet does not have TCP/UDP layers, we just ignore these packets
            pass

    def process_packet(self):
        self.sniffer = AsyncSniffer()
        self.sniffer._run(prn=self._process_packet, store=False)

    def get_connections(self):
        """A function that keeps listening for connections on this machine
        and adds them to `connection2pid` global variable"""
        while self.is_program_running:
            # using psutil, we can grab each connection's source and destination ports
            # and their process ID
            for c in psutil.net_connections():
                if c.laddr and c.raddr and c.pid:
                    # if local address, remote address and PID are in the connection
                    # add them to our global dictionary
                    self.connection2pid[(c.laddr.port, c.raddr.port)] = c.pid
                    self.connection2pid[(c.raddr.port, c.laddr.port)] = c.pid
            # sleep for a second, feel free to adjust this
            time.sleep(1)

    def print_pid2traffic(self):
        # initialize the list of processes
        processes = []
        for pid, traffic in self.pid2traffic.items():
            # `pid` is an integer that represents the process ID
            # `traffic` is a list of two values: total Upload and Download size in bytes
            try:
                # get the process object from psutil
                p = psutil.Process(pid)
                # get the name of the process, such as chrome.exe, etc.
                name = p.name()
                # get the time the process was spawned
                try:
                    create_time = datetime.fromtimestamp(p.create_time())
                except OSError:
                    # system processes, using boot time instead
                    create_time = datetime.fromtimestamp(psutil.boot_time())
                # construct our dictionary that stores process info

                process = {
                    "pid": pid,
                    "name": name,
                    "create_time": create_time,
                    "Upload": traffic[0],
                    "Download": traffic[1],
                    "Data Usage": traffic[0] + traffic[1],
                }
                try:
                    # calculate the upload and download speeds by simply subtracting the old stats from the new stats
                    process["Upload Speed"] = (
                        traffic[0] - self.global_df.at[pid, "Upload"]
                    )
                    process["Download Speed"] = (
                        traffic[1] - self.global_df.at[pid, "Download"]
                    )
                except (KeyError, AttributeError):
                    # If it's the first time running this function, then the speed is the current traffic
                    # You can think of it as if old traffic is 0
                    process["Upload Speed"] = traffic[0]
                    process["Download Speed"] = traffic[1]
                    process["Data Usage"] = traffic[0] + traffic[1]

                    # append the process to our processes list
                    processes.append(process)

            except psutil.NoSuchProcess:
                # if process is not found, simply continue to the next PID for now
                continue

        # Return the list of process dictionaries
        # print(f"processes:  {processes}")
        return processes

    def __init__(self):
        super().__init__()

        # Set up the GUI window
        self.setWindowTitle("App Data Usage Monitor")
        # self.setGeometry(100, 100, 800, 600)
        lay = QVBoxLayout(self)

        self.tableWidget = QTableWidget()
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        lay.addWidget(self.tableWidget)

        self.tableWidget.setRowCount(
            11
        )  # Increase the row count to accommodate the total row
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(
            [
                "PID",
                "Process Name",
                "Upload",
                "Download",
                "Create Time",
                "Data Usage",
            ]
        )

        self.startTimer(100)

        self.start_monitoring()

    def get_executable_path(self, process_name):
                    try:
                        for proc in psutil.process_iter(attrs=['name', 'exe']):
                            if proc.info['name'] == process_name:
                                return proc.info['exe']
                    except psutil.NoSuchProcess:
                        pass
                    return None
            
    def timerEvent(self, _):
        # Update the table with process data
        process_data = self.print_pid2traffic()
        total_upload = 0
        total_download = 0

        for i, process in enumerate(process_data):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(process["pid"])))
            
            #####
            # Extract the icon for the process
            
            executable_path = self.get_executable_path(process["name"])
            try:
                icons = win32gui.ExtractIconEx(executable_path, 0)  # Replace with the actual path to the executable
                icon = icons[0][0]
                width = height = 32

                # Create DC and bitmap and make them compatible.
                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, width, height)
                hdc = hdc.CreateCompatibleDC()
                hdc.SelectObject(hbmp)

                # Draw the icon.
                win32gui.DrawIconEx(
                    hdc.GetHandleOutput(),
                    0,
                    0,
                    icon,
                    width,
                    height,
                    0,
                    None,
                    0x0003,
                )

                # Destroy the icons.
                for iconList in icons:
                    for icon in iconList:
                        win32gui.DestroyIcon(icon)

                # Get the icon's bits and convert to a QImage.
                bitmapbits = hbmp.GetBitmapBits(True)
                image = QImage(
                    bitmapbits,
                    width,
                    height,
                    QImage.Format_ARGB32_Premultiplied,
                )

                # Write to and then load from a buffer to convert to PNG.
                buffer = QBuffer()
                buffer.setOpenMode(QIODevice.ReadWrite)
                image.save(buffer, "PNG")
                image.loadFromData(buffer.data(), "PNG")

                # Create a QPixmap from the QImage.
                pixmap = QPixmap.fromImage(image)

                # Create a table widget item for the process name
                process_name_item = QTableWidgetItem(process["name"])
                # Set the icon for the process name item
                process_name_item.setIcon(QIcon(pixmap))
                self.tableWidget.setItem(i, 1, process_name_item)
            except Exception as e:
                pass
            ###
            
            #self.tableWidget.setItem(i, 2, QTableWidgetItem(process["name"]))
            self.tableWidget.setItem(
                i, 2, QTableWidgetItem(self.get_size(process["Upload"]))
            )
            self.tableWidget.setItem(
                i, 3, QTableWidgetItem(self.get_size(process["Download"]))
            )
            self.tableWidget.setItem(
                i,
                4,
                QTableWidgetItem(process["create_time"].strftime("%Y-%m-%d %H:%M:%S")),
            )

            # Calculate and display the total data usage
            total_data_usage = process["Upload"] + process["Download"]
            self.tableWidget.setItem(
                i,
                5,
                QTableWidgetItem(
                    self.get_size(
                        process["Data Usage"]
                        if total_data_usage == 0
                        else total_data_usage
                    )
                ),
            )

            # Accumulate total upload and download
            total_upload += process["Upload"]
            total_download += process["Download"]

        # Display the total data usage at the top
        self.tableWidget.setItem(10, 0, QTableWidgetItem("Total Data Usage"))
        self.tableWidget.setItem(
            10, 5, QTableWidgetItem(self.get_size(total_upload + total_download))
        )

    def start_monitoring(self):
        self.is_program_running = True
        # Start the printing thread
        printing_thread = Thread(target=self.print_pid2traffic)
        printing_thread.start()
        # Start the connections thread
        connections_thread = Thread(target=self.get_connections)
        connections_thread.start()
        # Start the sniffing in a separate thread to prevent GUI freezing
        sniff_thread = Thread(
            target=self.process_packet,
            # target=lambda: sniff(prn=self.process_packet, store=False)
        )
        sniff_thread.start()

    def closeEvent(self, _):
        self.is_program_running = False
        self.sniffer.continue_sniff = False
        QApplication.instance().quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = NetworkUsageGUI()
    ex.show()
    sys.exit(app.exec())
