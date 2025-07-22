import sys
import serial
import serial.tools.list_ports
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QMessageBox, QComboBox, QGroupBox
)
from PyQt5.QtCore import Qt

SCB_REGISTERS = {
    "CPUID": 0xE000ED00,
    "ICSR":  0xE000ED04,
    "VTOR":  0xE000ED08,
    "AIRCR": 0xE000ED0C,
    "SCR":   0xE000ED10,
    "CCR":   0xE000ED14
}

class STM32Terminal(QWidget):
    def __init__(self):
        """Initialize the GUI and serial variables."""

        super().__init__()
        self.ser = None
        self.init_ui()

    def init_ui(self):
        """Build and arrange all the GUI widgets and layouts."""

        self.setWindowTitle("STM32 UART Register Tool")

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter COM port (e.g., COM5)")
        self.baud_select = QComboBox()
        self.baud_select.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baud_select.setCurrentText("115200")

        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn = connect_btn

        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn = disconnect_btn
        self.disconnect_btn.setEnabled(False)

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        port_layout.addWidget(self.port_input)
        port_layout.addWidget(QLabel("Baud:"))
        port_layout.addWidget(self.baud_select)
        port_layout.addWidget(connect_btn)
        port_layout.addWidget(disconnect_btn)

        scb_group = QGroupBox("SCB Registers")
        scb_layout = QHBoxLayout()
        self.scb_buttons = []
        for name, addr in SCB_REGISTERS.items():
            btn = QPushButton(f"Read {name}")
            btn.clicked.connect(lambda _, a=addr, n=name: self.read_scb_register(a, n))
            btn.setEnabled(False)
            self.scb_buttons.append(btn)
            scb_layout.addWidget(btn)
        scb_group.setLayout(scb_layout)

        self.read_addr_input = QLineEdit()
        self.read_addr_input.setPlaceholderText("Enter address (hex e.g. 0x48000010)")
        read_btn = QPushButton("Read Register")
        read_btn.clicked.connect(self.read_custom_register)
        read_btn.setEnabled(False)
        self.read_btn = read_btn

        read_layout = QHBoxLayout()
        read_layout.addWidget(self.read_addr_input)
        read_layout.addWidget(read_btn)

        self.write_addr_input = QLineEdit()
        self.write_addr_input.setPlaceholderText("Enter address (hex)")
        self.write_value_input = QLineEdit()
        self.write_value_input.setPlaceholderText("Enter value (hex)")
        write_btn = QPushButton("Write Register")
        write_btn.clicked.connect(self.write_custom_register)
        write_btn.setEnabled(False)
        self.write_btn = write_btn

        write_layout = QHBoxLayout()
        write_layout.addWidget(self.write_addr_input)
        write_layout.addWidget(self.write_value_input)
        write_layout.addWidget(write_btn)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        main_layout = QVBoxLayout()
        main_layout.addLayout(port_layout)
        main_layout.addWidget(scb_group)
        main_layout.addLayout(read_layout)
        main_layout.addLayout(write_layout)
        main_layout.addWidget(QLabel("Log:"))
        main_layout.addWidget(self.log)
        self.setLayout(main_layout)

    def connect_serial(self):
        """
        Attempt to open the serial port with user-specified COM port and baud rate.
        On success, enable register read/write buttons and update log.
        On failure, show error message.
        """

        port = self.port_input.text().strip()
        baud = int(self.baud_select.currentText())
        if not port:
            self.show_error("Please enter a COM port (e.g., COM5).")
            return
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.log.append(f"Connected to {port} at {baud} baud.")
            self.set_connected_state(True)
        except serial.SerialException as e:
            self.show_error(f"Failed to open serial port: {e}")

    def disconnect_serial(self):
        """
        Close the open serial port, disable register buttons,
        and update log to indicate disconnection.
        """

        if self.ser and self.ser.is_open:
            self.ser.close()
            self.log.append("Disconnected.")
        self.set_connected_state(False)

    def set_connected_state(self, connected):
        """
        Enable or disable UI buttons based on connection status.
        Prevent register operations when disconnected.
        """

        # Enable or disable buttons based on connection
        for btn in self.scb_buttons:
            btn.setEnabled(connected)
        self.read_btn.setEnabled(connected)
        self.write_btn.setEnabled(connected)
        self.connect_btn.setEnabled(not connected)
        self.disconnect_btn.setEnabled(connected)

    def send_command(self, cmd):
        """
        Send a command string to the STM32 UART.
        Wait briefly and read the response line.
        Log the command and response.
        Returns the response string.
        """

        if not self.ser or not self.ser.is_open:
            self.show_error("Serial port not open.")
            return "ERROR"
        try:
            self.ser.write(cmd.encode())
            time.sleep(0.05)
            response = self.ser.readline().decode(errors='ignore').strip()
            self.log.append(f">> {cmd.strip()}\n{response}")
            return response
        except Exception as e:
            self.show_error(f"Serial error: {e}")
            return "ERROR"

    def read_scb_register(self, address, name):
        """
        Format and send a 'read' command for a known SCB register.
        Log the register name and response.
        """

        cmd = f"read 0x{address:X}\r\n"
        response = self.send_command(cmd)
        self.log.append(f"{name}: {response}")

    def read_custom_register(self):
        """
        Read address from user input, validate hex format.
        Send read command to device and log response.
        Show error if input invalid.
        """

        addr_str = self.read_addr_input.text().strip()
        try:
            addr = int(addr_str, 16)
            cmd = f"read 0x{addr:X}\r\n"
            response = self.send_command(cmd)
            self.log.append(f"Read 0x{addr:X}: {response}")
        except ValueError:
            self.show_error("Invalid address format. Use hex (e.g., 0x48000010).")

    def write_custom_register(self):
        """
        Read address and value from user input, validate hex format.
        Send write command to device and log response.
        Show error if input invalid.
        """

        addr_str = self.write_addr_input.text().strip()
        val_str = self.write_value_input.text().strip()
        try:
            addr = int(addr_str, 16)
            val = int(val_str, 16)
            cmd = f"write 0x{addr:X} 0x{val:X}\r\n"
            response = self.send_command(cmd)
            self.log.append(f"Wrote 0x{val:X} to 0x{addr:X}: {response}")
        except ValueError:
            self.show_error("Invalid address or value format. Use hex (e.g., 0x48000010).")

    def show_error(self, msg):
        """
        Display a critical error popup dialog.
        Also append error message to the log window.
        """

        QMessageBox.critical(self, "Error", msg)
        self.log.append(f"{msg}")

    def closeEvent(self, event):
        """
        Override QWidget close event to safely close serial port on exit.
        """

        if self.ser and self.ser.is_open:
            self.ser.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = STM32Terminal()
    win.resize(700, 500)
    win.show()
    sys.exit(app.exec_())
