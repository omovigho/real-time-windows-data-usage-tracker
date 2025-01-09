import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, 
    QPushButton, QHBoxLayout, QMessageBox
)

class SettingsWindow(QDialog):
    SETTINGS_FILE = "settings_data.json"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        self.layout = QVBoxLayout(self)
        
        # Load settings
        self.settings = self.load_settings()

        # Components
        self.create_ui()

    def load_settings(self):
        if not os.path.exists(self.SETTINGS_FILE):
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump({
                    "data-limit": None,
                    "exceeded-data-limit": None,
                    "enable-data-limit": False,
                    "enable-alert-message": False
                }, f)
        with open(self.SETTINGS_FILE, "r") as f:
            return json.load(f)

    def save_settings(self):
        with open(self.SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f)

    def create_ui(self):
        # Set Data Limit
        self.add_data_limit_ui()

        # Enable Data Limit
        self.add_toggle_ui("Enable Data Limit", "enable-data-limit")

        # Enable Data Limit Alert
        self.add_toggle_ui("Enable Data Limit Alert", "enable-alert-message")

        # Exceeded Data Limit
        self.add_exceeded_limit_ui()

        # Buttons
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        self.layout.addWidget(save_btn)

    def add_data_limit_ui(self):
        label = QLabel("Set Data Limit (KB, MB, GB):")
        self.layout.addWidget(label)

        self.data_limit_input = QLineEdit(self)
        self.layout.addWidget(self.data_limit_input)

        self.data_limit_unit = QComboBox(self)
        self.data_limit_unit.addItems(["KB", "MB", "GB"])
        self.layout.addWidget(self.data_limit_unit)

        set_btn = QPushButton("Set Data Limit")
        set_btn.clicked.connect(self.set_data_limit)
        self.layout.addWidget(set_btn)

    def set_data_limit(self):
        try:
            value = int(self.data_limit_input.text())
            unit = self.data_limit_unit.currentText()
            multiplier = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}[unit]
            self.settings["data-limit"] = value * multiplier
            QMessageBox.information(self, "Success", "Data Limit Set Successfully!")
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid number.")

    def add_toggle_ui(self, label_text, setting_key):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        layout.addWidget(label)

        toggle = QCheckBox("Enable")
        toggle.setChecked(self.settings[setting_key])
        toggle.stateChanged.connect(lambda state: self.toggle_setting(setting_key, state))
        layout.addWidget(toggle)

        self.layout.addLayout(layout)

    def toggle_setting(self, key, state):
        self.settings[key] = state == 2  # True if checked, else False

    def add_exceeded_limit_ui(self):
        label = QLabel("Set Exceeded Data Limit (KB, MB, GB):")
        self.layout.addWidget(label)

        self.exceeded_limit_input = QLineEdit(self)
        self.layout.addWidget(self.exceeded_limit_input)

        self.exceeded_limit_unit = QComboBox(self)
        self.exceeded_limit_unit.addItems(["KB", "MB", "GB", "Unlimited"])
        self.layout.addWidget(self.exceeded_limit_unit)

        set_btn = QPushButton("Set Exceeded Data Limit")
        set_btn.clicked.connect(self.set_exceeded_limit)
        self.layout.addWidget(set_btn)

    def set_exceeded_limit(self):
        unit = self.exceeded_limit_unit.currentText()
        if unit == "Unlimited":
            self.settings["exceeded-data-limit"] = "Unlimited"
        else:
            try:
                value = int(self.exceeded_limit_input.text())
                multiplier = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}[unit]
                self.settings["exceeded-data-limit"] = value * multiplier
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter a valid number.")
        QMessageBox.information(self, "Success", "Exceeded Data Limit Set Successfully!")
