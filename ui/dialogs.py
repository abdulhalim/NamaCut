# --------------------------------------------------
# Dialogs Module
# Contains dialog windows for settings and about information
# --------------------------------------------------

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox,
    QTabWidget, QWidget, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import qtawesome as qta

# --------------------------------------------------
# SettingsDialog Class
# Basic settings dialog for output format and quality selection
# --------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Basic Settings")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.init_ui()

    # --------------------------------------------------
    # UI Initialization
    # --------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout()

        # Format selection section
        format_layout = QVBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Video - MP4 (H.264)", 
            "Video - MKV (H.264)", 
            "Video - WebM (VP9)", 
            "Audio - MP3", 
            "Audio - AAC", 
            "Audio - FLAC"
        ])
        format_layout.addWidget(self.format_combo)

        # Quality selection section
        quality_layout = QVBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Original", "4K", "1080p", "720p", "480p"
        ])
        quality_layout.addWidget(self.quality_combo)

        layout.addLayout(format_layout)
        layout.addLayout(quality_layout)
        layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    # --------------------------------------------------
    # Settings Retrieval
    # Convert UI selections to settings dictionary
    # --------------------------------------------------
    def get_settings(self):
        format_text = self.format_combo.currentText()
        
        # Parse audio formats
        if "MP3" in format_text:
            return {"audio_output_format": "mp3"}
        elif "AAC" in format_text:
            return {"audio_output_format": "aac"}
        elif "FLAC" in format_text:
            return {"audio_output_format": "flac"}
        
        # Parse video formats
        elif "MP4" in format_text:
            return {"format_index": 1, "video_codec": "H264"}
        elif "MKV" in format_text:
            return {"format_index": 2, "video_codec": "H264"} 
        elif "WebM" in format_text:
            return {"format_index": 3, "video_codec": "VP9"}
        
        return {}

# --------------------------------------------------
# AboutDialog Class
# Application information and credits dialog
# --------------------------------------------------
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About NamaCut")
        self.setModal(True)
        self.setFixedSize(400, 480)
        
        # Add border to the dialog
        self.setStyleSheet("""
            QDialog {
                border: 2px solid #3f8e93;
            }
        """)
        
        self.init_ui()

    # --------------------------------------------------
    # UI Initialization
    # --------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 30, 20, 20)

        # Application icon section
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)

        # Try to load the logo image
        pixmap = QPixmap("img/logo.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Fallback to qtawesome icon
            try:
                icon = qta.icon('fa5s.film', color='#2c3e50')
                pixmap = icon.pixmap(128, 128)
                icon_label.setPixmap(pixmap)
            except Exception as e:
                print(f"Error loading fallback icon: {e}")
                icon_label.setText("🎬")
                icon_label.setStyleSheet("font-size: 96px;")

        # Application information section
        name_label = QLabel("NamaCut")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")

        version_label = QLabel("Version 2.0.26")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")

        description_label = QLabel("Simple Video Cutter and Editor")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("font-size: 14px; color: #34495e;")

        website_label = QLabel('<a href="https://pourdaryaei.ir" style="color: #3498db; text-decoration: none;">Pourdaryaei.ir</a>')
        website_label.setAlignment(Qt.AlignCenter)
        website_label.setOpenExternalLinks(True)

        author_label = QLabel("Developed by Abdulhalim Pourdaryaei")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")

        license_label = QLabel("License: MIT Open Source")
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")

        # Add all widgets to layout
        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        layout.addWidget(version_label)
        layout.addWidget(description_label)
        layout.addWidget(website_label)
        layout.addWidget(author_label)
        layout.addWidget(license_label)

        # Close button
        close_button = QDialogButtonBox(QDialogButtonBox.Close)
        close_button.rejected.connect(self.reject)
        layout.addWidget(close_button)

        self.setLayout(layout)