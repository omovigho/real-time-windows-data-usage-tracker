# Real-Time Windows Data Usage Tracker

## Overview

The **Real-Time Windows Data Usage Tracker** is a Python-based application that monitors and tracks internet data usage on Windows devices in real-time. It provides insights into data consumption and allows users to control Wi-Fi connectivity effectively.

## Features

- Real-time monitoring of data usage.
- Wi-Fi control capabilities (enable/disable connection programmatically).
- Configurable settings for tracking preferences.
- Lightweight and efficient, suitable for continuous usage.

## Project Structure

The project consists of the following core files:

- **`app_data_usage.py`** – Tracks real-time data usage.
- **`data_wifi_control.py`** – Manages Wi-Fi connectivity.
- **`settings.py`** – Configures tracking preferences.
- **`main.py`** - Calculate the total internet data usage.
- **`requirements.txt`** – Contains all required dependencies.

## Installation

### Prerequisites

Ensure you have Python installed on your system. You can download it from [Python's official website](https://www.python.org/).

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/omovigho/real-time-windows-data-usage-tracker.git
   cd real-time-windows-data-usage-tracker
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the tracker by executing the main script:

```bash
python app_data_usage.py
```

To control Wi-Fi settings, use:

```bash
python data_wifi_control.py
```

## Configuration

Modify `settings.py` to adjust monitoring preferences.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m "Add new feature"`).
4. Push to your branch (`git push origin feature-name`).
5. Create a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For any inquiries, please open an issue or reach out via email at [danagofure330@gmail.com](danagofure330@gmail.com).
