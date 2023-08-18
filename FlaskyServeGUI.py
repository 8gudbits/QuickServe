from PyQt5.QtWidgets import QLineEdit, QMainWindow, QFrame, QPushButton, QMessageBox, QApplication
from PyQt5.QtGui import QColor, QPalette, QPixmap, QPainter, QFont, QIcon
from PyQt5.QtCore import Qt
from pyFlaskyServe import ServerThread
import socket
import sys

class PlaceholderLineEdit(QLineEdit):
    """Custom QLineEdit widget with placeholder text and color.

    Args:
        placeholder (str): Placeholder text to display.
        color (str): Color of the placeholder text.
        parent (QWidget): Parent widget.

    Attributes:
        placeholder (str): Placeholder text to display.
        placeholder_color (QColor): Color of the placeholder text.
        default_fg_color (QColor): Default foreground text color.
        user_interaction (bool): Flag indicating user interaction.
        user_input (bool): Flag indicating user input.

    Signals:
        None

    """
    def __init__(self, placeholder='', color='gray', parent=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.placeholder_color = QColor(color)
        self.default_fg_color = self.palette().color(QPalette.Text)  # Get the default text color from the palette
        self.user_interaction = False
        self.user_input = False

        self.setPlaceholderText(self.placeholder)
        self.setPlaceholderColor(color)

        self.setStyleSheet(
            '''
            QLineEdit {
                background-color: #252525;
                color: white;
                border: none;
                border-bottom: 1px solid transparent;
                selection-background-color: #3D3D3D;
            }

            QLineEdit:focus {
                border-bottom: 1px solid #007BFF;
            }
            '''
        )

        self.textChanged.connect(self.on_text_changed)

    def setPlaceholderColor(self, color):
        """Set the color of the placeholder text.

        Args:
            color (str): Color of the placeholder text.

        Returns:
            None
        """
        palette = self.palette()
        palette.setColor(QPalette.PlaceholderText, QColor(color))  # Set the color of placeholder text in the palette
        self.setPalette(palette)  # Apply the updated palette to the widget
    
    def focusInEvent(self, event):
        """Event handler for focus in.

        Args:
            event (QFocusEvent): Focus event.

        Returns:
            None
        """
        super().focusInEvent(event)

        if self.text() == self.placeholder:
            self.clear()  # Clear the text if it's the placeholder text
            self.setPalette(self.default_palette())  # Restore the default text color
        
        self.user_interaction = True  # Indicate that user interaction is occurring

    def focusOutEvent(self, event):
        """Event handler for focus out.

        Args:
            event (QFocusEvent): Focus event.

        Returns:
            None
        """
        super().focusOutEvent(event)
        
        if not self.text():
            self.setPlaceholderText(self.placeholder)  # Restore the placeholder text if text is empty
            self.setPalette(self.placeholder_palette())  # Apply placeholder color to text
        
        self.user_interaction = False  # Indicate that user interaction has ended

    def on_text_changed(self):
        """Slot for handling text changed event.

        Args:
            None

        Returns:
            None
        """
        if not self.user_input:
            self.user_input = True  # Indicate that the user has input some text

    def default_palette(self):
        """Get the default palette.

        Args:
            None

        Returns:
            QPalette: Default palette.
        """
        palette = self.palette()
        palette.setColor(QPalette.Text, self.default_fg_color)  # Set the default text color in the palette
        return palette

    def placeholder_palette(self):
        """Get the placeholder palette.

        Args:
            None

        Returns:
            QPalette: Placeholder palette.
        """
        palette = self.palette()
        palette.setColor(QPalette.Text, self.placeholder_color)  # Set the placeholder text color in the palette
        return palette

class MainWindow(QMainWindow):
    """Main application window class.

    Args:
        None

    Attributes:
        server_thread (ServerThread): Server thread instance.
        host (str): Server host address.
        hostname (str): Local hostname.
        local_ip (str): Local IP address.
        serve_port (int): Server port number.

    Signals:
        None
    """
    def __init__(self):
        super().__init__()

        # Initialize attributes
        self.server_thread = None
        self.host = "0.0.0.0"
        self.hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(self.hostname)
        self.serve_port = 5000

        # Set up main window properties
        self.setWindowTitle("pyFlaskyServe")
        self.setFixedSize(250, 134)
        self.setWindowOpacity(0.95)

        # Create and set window icon
        app_icon_emoji = QPixmap(32, 32)
        app_icon_emoji.fill(Qt.transparent)
        painter = QPainter(app_icon_emoji)
        painter.setFont(QFont("Segoe UI Emoji", 20))
        painter.drawText(app_icon_emoji.rect(), Qt.AlignCenter, "\U0001F310")
        painter.end()
        self.setWindowIcon(QIcon(app_icon_emoji))

        # Create and position UI elements
        self.copy_button_frame = QFrame(self)
        self.copy_button_frame.setGeometry(10, 10, 230, 24)

        self.copy_button = QPushButton(self.copy_button_frame)
        self.copy_button.setGeometry(0, 0, 230, 24)
        self.copy_button.setText(f"Copy IP:Port ({self.local_ip}:{self.serve_port})")
        self.copy_button.clicked.connect(self.copy_button_clicked)

        self.port_entry_frame = QFrame(self)
        self.port_entry_frame.setGeometry(10, 40, 230, 24)

        self.port_entry = PlaceholderLineEdit(placeholder="Enter port number (default: 5000)",
                                              color='gray', parent=self.port_entry_frame)
        self.port_entry.setGeometry(0, 0, 230, 24)

        self.start_button_frame = QFrame(self)
        self.start_button_frame.setGeometry(10, 70, 230, 24)

        self.start_button = QPushButton(self.start_button_frame)
        self.start_button.setGeometry(0, 0, 230, 24)
        self.start_button.setText("Start Flasky Serve")
        self.start_button.clicked.connect(self.start_button_clicked)

        self.stop_button_frame = QFrame(self)
        self.stop_button_frame.setGeometry(10, 100, 230, 24)

        self.stop_button = QPushButton(self.stop_button_frame)
        self.stop_button.setGeometry(0, 0, 230, 24)
        self.stop_button.setText("Exit Flasky Serve")
        self.stop_button.setDisabled(True)
        self.stop_button.clicked.connect(self.stop_button_clicked)

        # Set color palette for UI elements
        self.set_color_palette()

    def set_color_palette(self):
        """Set the color palette for the application.

        Args:
            None

        Returns:
            None
        """
        # Define a dark color palette for UI elements
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(24, 24, 24))
        dark_palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)

        # Apply the defined dark color palette to the main window
        self.setPalette(dark_palette)

        dark_stylesheet = """
            QComboBox {
                background-color: #252525;
                color: white;
                selection-background-color: #3D3D3D;
                border: 2px solid #3D3D3D;
                border-radius: 10px;
                padding: 2px 2px 2px 4px;
            }
            QComboBox:!editable {
                color: white;
            }
            QComboBox QAbstractItemView {
                background-color: #252525;
                color: white;
                selection-background-color: #3D3D3D;
                selection-color: white;
            }
            QLineEdit {
                background-color: #252525;
                color: white;
                selection-background-color: #3D3D3D;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                padding: 2px;
            }
            QPushButton {
                background-color: #383838;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #2F2F2F;
            }
            QPushButton:pressed {
                background-color: #202020;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """
        # Apply a dark stylesheet to UI elements
        self.setStyleSheet(dark_stylesheet)

    def copy_button_clicked(self):
        """Slot for handling copy button click event.

        Args:
            None

        Returns:
            None
        """
        # Get the entered port number and validate it
        serve_port_str = self.port_entry.text()
        if not serve_port_str.strip():
            serve_port = 5000
        else:
            try:
                serve_port = int(serve_port_str.strip())
                if serve_port < 1024 or serve_port > 65535:
                    # Display an error message if port is out of range
                    QMessageBox.critical(self, "Error: Port Out of Range",
                                         "Port should be a number between 1024 and 65535")
                    self.port_entry.clear()
                    serve_port = 5000
            except ValueError:
                # Display an error message if invalid port format
                QMessageBox.critical(self, "Error: Invalid Port",
                                     "Port should be a number between 1024 and 65535")
                self.port_entry.clear()
                serve_port = 5000

        # Generate and copy IP:Port to clipboard
        ip_port = f"{self.local_ip}:{serve_port}"
        self.copy_button.setText(f"Copy IP:Port ({self.local_ip}:{serve_port})")
        clipboard = QApplication.clipboard()
        clipboard.setText(ip_port)

    def start_button_clicked(self):
        """Slot for handling start button click event.

        Args:
            None

        Returns:
            None
        """
        # Get the entered port number and validate it
        serve_port_str = self.port_entry.text()
        if not serve_port_str.strip():
            serve_port = 5000
        else:
            try:
                serve_port = int(serve_port_str.strip())
                if serve_port < 1024 or serve_port > 65535:
                    # Display an error message if port is out of range
                    QMessageBox.critical(self, "Error: Port Out of Range",
                                         "Port should be a number between 1024 and 65535")
                    self.port_entry.clear()
                    return
            except ValueError:
                # Display an error message if invalid port format
                QMessageBox.critical(self, "Error: Invalid Port",
                                     "Port should be a number between 1024 and 65535")
                self.port_entry.clear()
                return

        # Update copy button text and UI elements
        self.copy_button.setText(f"Copy IP:Port ({self.local_ip}:{serve_port})")
        self.start_button.setDisabled(True)
        self.stop_button.setEnabled(True)

        QMessageBox.warning(self, "Warning", "Starting the server might not work if there's already a server on the same port or if the port is busy.")

        # Start the server thread if not already running
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = ServerThread(self.host, serve_port)
            self.server_thread.daemon = True
            self.server_thread.start()

    def stop_button_clicked(self):
        """Slot for handling stop button click event.

        Args:
            None

        Returns:
            None
        """
        self.close()

def main():
    """Main function to run the application.

    Args:
        None

    Returns:
        None
    """
    Qapp = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    main_window.activateWindow()
    main_window.raise_()

    sys.exit(Qapp.exec_())

if __name__ == '__main__':
    main()
