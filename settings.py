import json
import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt


class ToggleButton(QPushButton):
    def __init__(self, text_on="ON", text_off="OFF", parent=None):
        super().__init__(parent)
        self.text_on = text_on
        self.text_off = text_off
        self.settings_data = SettingsWindow.load_settings(self)
        self.is_on = self.settings_data["enable-alert-message"]  # Default state is OFF
        self.setCheckable(True)
        self.update_button()

        # Connect toggle action
        self.clicked.connect(self.toggle_state)
        
    def toggle_state(self):
        self.is_on = not self.is_on
        self.update_button()

    def update_button(self):
        self.setText(self.text_on if self.is_on else self.text_off)
        self.setStyleSheet(self.get_stylesheet())
        
    def get_stylesheet(self):
        if self.is_on:
            return """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 15px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border-radius: 15px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #e53935;
                }
            """
    
    '''self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
            QPushButton:checked:hover {
                background-color: #da190b;
            }
        """)'''
        
class SettingsWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        self.settings_data = self.load_settings()
        SETTINGS_FILE = "settings_data.json"

        # Main layout
        self.layout = QVBoxLayout(self)

        # Data Limit Section
        self.add_data_limit_section()

        # Exceeded Data Limit Section
        self.add_exceeded_data_limit_section()

        # Save Button
        self.add_save_button()
        
    # Getting the size of the data in different format    
    def get_size(self, bytes: int) -> str:
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < 1024:
                return f"{bytes:.2f}{unit}B"
            bytes /= 1024

    def add_data_limit_section(self):
        # Data Limit Input
        data_limit_layout = QHBoxLayout()
        self.data_limit_input = QLineEdit()
        self.data_limit_input.setPlaceholderText("Enter data limit")
        self.data_limit_unit = QComboBox()
        self.data_limit_unit.addItems(["KB", "MB", "GB"])
        self.data_limit_button = QPushButton("Set Data Limit")
        self.data_limit_button.clicked.connect(self.set_data_limit)

        data_limit_layout.addWidget(QLabel("Data Limit:"))
        data_limit_layout.addWidget(self.data_limit_input)
        data_limit_layout.addWidget(self.data_limit_unit)
        data_limit_layout.addWidget(self.data_limit_button)
        self.layout.addLayout(data_limit_layout)

        # Display Current Data Limit
        if self.settings_data.get("data-limit", 'Null') == "Null":
            self.current_data_limit_label = QLabel(f"Current Data Limit: Null")
        else:
            data_int  = int((self.settings_data.get("data-limit", 'Null')))
            #self.current_data_limit_label = QLabel(f"Current Data Limit: {self.settings_data.get('data-limit', 'Null')}")
            self.current_data_limit_label = QLabel(f"Current Data Limit: {self.get_size(data_int)}")
       
        self.layout.addWidget(self.current_data_limit_label)

        # Enable Data Limit Toggle
        '''self.enable_data_limit_checkbox = QCheckBox("Enable Data Limit")
        self.enable_data_limit_checkbox.setChecked(self.settings_data.get("enable-data-limit", False))
        self.layout.addWidget(self.enable_data_limit_checkbox)'''
        # Enable Data Limit Toggle
        self.enable_data_limit_toggle = ToggleButton("ON", "OFF")
        self.layout.addWidget(QLabel("Enable Data Limit:"))
        self.layout.addWidget(self.enable_data_limit_toggle, alignment=Qt.AlignLeft)

    def add_exceeded_data_limit_section(self):
        # Exceeded Data Limit Input
        exceeded_limit_layout = QHBoxLayout()
        self.exceeded_limit_input = QLineEdit()
        self.exceeded_limit_input.setPlaceholderText("Enter exceeded data limit")
        self.exceeded_limit_unit = QComboBox()
        self.exceeded_limit_unit.addItems(["KB", "MB", "GB"])
        self.unlimited_checkbox = QCheckBox("Unlimited")
        self.unlimited_checkbox.setChecked(self.settings_data.get("exceeded-data-limit", "Unlimited") == "Unlimited")

        exceeded_limit_layout.addWidget(QLabel("Exceeded Limit:"))
        exceeded_limit_layout.addWidget(self.exceeded_limit_input)
        exceeded_limit_layout.addWidget(self.exceeded_limit_unit)
        exceeded_limit_layout.addWidget(self.unlimited_checkbox)
        self.layout.addLayout(exceeded_limit_layout)

        # Display Current Exceeded Data Limit
        if self.settings_data.get("exceeded-data-limit", 'Null') == "Unlimited":
            self.current_exceeded_limit_label = QLabel(f"Exceeded Data Limit: Unlimited")
        else:
            exceeded_data_int  = int((self.settings_data.get("exceeded-data-limit", 'Null')))
            self.current_exceeded_limit_label = QLabel(f"Exceeded Data Limit: {self.get_size(exceeded_data_int)}")
        self.layout.addWidget(self.current_exceeded_limit_label)

        '''# Enable Data Limit Alert Toggle
        self.enable_alert_checkbox = QCheckBox("Enable Data Limit Alert")
        self.enable_alert_checkbox.setChecked(self.settings_data.get("enable-alert-message", False))
        self.layout.addWidget(self.enable_alert_checkbox)'''
        # Enable Data Limit Alert Toggle
        self.enable_alert_toggle = ToggleButton("ON", "OFF")
        self.layout.addWidget(QLabel("Enable Data Limit Alert:"))
        self.layout.addWidget(self.enable_alert_toggle, alignment=Qt.AlignLeft)

    def add_save_button(self):
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(save_button, alignment=Qt.AlignRight)

    def set_data_limit(self):
        try:
            value = int(self.data_limit_input.text())
            if value < 1:
                raise ValueError("Data limit must be greater than or equal to 1.")
            
            unit = self.data_limit_unit.currentText()
            value_in_bytes = value * 1024 ** ["BYTES","KB", "MB", "GB"].index(unit)
            self.settings_data["data-limit"] = value_in_bytes
            self.current_data_limit_label.setText(f"Current Data Limit: {value_in_bytes} bytes")
            QMessageBox.information(self, "Success", "Data limit set successfully.")
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_settings(self):
        # Save Enable Data Limit and Alert settings
        #self.settings_data["enable-data-limit"] = self.enable_data_limit_checkbox.isChecked()
        #self.settings_data["enable-alert-message"] = self.enable_alert_checkbox.isChecked()
        self.settings_data["enable-data-limit"] = self.enable_data_limit_toggle.is_on
        self.settings_data["enable-alert-message"] = self.enable_alert_toggle.is_on
        #QMessageBox.information(self, "Settings Saved", f"Enable Data Limit: {enable_data_limit}\nEnable Alert: {enable_alert}")
        #self.close()

        # Save Exceeded Data Limit
        if self.unlimited_checkbox.isChecked():
            self.settings_data["exceeded-data-limit"] = "Unlimited"
        else:
            try:
                value = int(self.exceeded_limit_input.text())
                if value < 1:
                    raise ValueError("Exceeded data limit must be greater than or equal to 1.")

                unit = self.exceeded_limit_unit.currentText()
                value_in_bytes = value * 1024 ** ["BYTES","KB", "MB", "GB"].index(unit)
                self.settings_data["exceeded-data-limit"] = value_in_bytes
            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))
                return

        # Save settings to file
        self.save_settings_to_file()
        QMessageBox.information(self, "Success", "Settings saved successfully.")
        self.close()  # Close the settings window

    def load_settings(self):
        if not os.path.exists("settings_data.json"):
            with open("settings_data.json", "w") as f:
                json.dump({
                    "data-limit": 'Null',
                    "exceeded-data-limit": 'Unlimited',
                    "enable-data-limit": False,
                    "enable-alert-message": False
                }, f)
        try:
            with open("settings_data.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_settings_to_file(self):
        with open("settings_data.json", "w") as f:
            json.dump(self.settings_data, f, indent=4)


