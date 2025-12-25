# --------------------------------------------------
# Video Editor Main Window
# This module contains the main window and UI components for NamaCut video editor
# --------------------------------------------------

import os
import sys
import cv2
import time
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QFileDialog, QMessageBox, QProgressBar,
                             QComboBox, QGroupBox, QGridLayout, QSpinBox,
                             QWidget, QSplitter, QDialog, QApplication, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPainter, QColor, QTransform
from PyQt5.QtMultimedia import QMediaContent
import qtawesome as qta

from ui.widgets import IconButton, VideoPlayer
from ui.dialogs import AboutDialog
from ui.advanced_settings import AdvancedSettingsDialog
from core.settings_manager import SettingsManager
from core.video_processor import VideoProcessor
from core.video_transformer import VideoTransformer
from core.utils import *

APP_VERSION = "2026"
APP_NAME = "NamaCut"

# --------------------------------------------------
# CustomSlider Class
# Enhanced QSlider with time range visualization
# --------------------------------------------------
class CustomSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.start_time = 0
        self.end_time = 0
        self.total_duration = 0

    def set_time_range(self, start, end, total):
        self.start_time = start
        self.end_time = end
        self.total_duration = total
        self.update()

    def reset(self):
        self.start_time = 0
        self.end_time = 0
        self.total_duration = 0
        self.setValue(0)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.total_duration <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        start_time = min(self.start_time, self.total_duration)
        end_time = min(self.end_time, self.total_duration)

        start_pos = (start_time / self.total_duration) * self.width()
        end_pos = (end_time / self.total_duration) * self.width()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(63, 142, 147, 100))
        painter.drawRect(int(start_pos), 0, int(end_pos - start_pos), self.height())

        painter.setBrush(QColor(255, 0, 0, 50))

        if start_pos > 0:
            painter.drawRect(0, 0, int(start_pos), self.height())

        if end_pos < self.width():
            painter.drawRect(int(end_pos), 0, int(self.width() - end_pos), self.height())

# --------------------------------------------------
# ExportCompleteDialog Class
# Dialog shown when video export completes successfully
# --------------------------------------------------
class ExportCompleteDialog(QDialog):
    def __init__(self, parent=None, output_file=None):
        super().__init__(parent)
        self.output_file = output_file
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Export Complete")
        self.setFixedSize(450, 240)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        icon_layout = QHBoxLayout()
        icon_label = QLabel()
        try:
            icon = qta.icon('fa5s.check-circle', color='#27ae60')
            pixmap = icon.pixmap(36, 36)
            icon_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setFixedSize(36, 36)
            icon_label.setText("✓")
            icon_label.setStyleSheet("font-size: 24px; color: #27ae60;")

        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()

        layout.addLayout(icon_layout)

        message_label = QLabel("Video exported successfully!")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(message_label)

        file_label = QLabel(f"File: {os.path.basename(self.output_file)}")
        file_label.setAlignment(Qt.AlignCenter)
        file_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        file_label.setWordWrap(True)
        layout.addWidget(file_label)

        layout.addSpacing(15)

        button_layout = QHBoxLayout()

        self.open_folder_btn = IconButton('fa5s.folder-open', ' Open Output Folder')
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setFixedSize(160, 36)

        self.close_btn = IconButton('fa5s.times', ' Close')
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setFixedSize(100, 36)

        button_layout.addStretch()
        button_layout.addWidget(self.open_folder_btn)
        button_layout.addWidget(self.close_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def open_output_folder(self):
        if self.output_file and os.path.exists(self.output_file):
            output_dir = os.path.dirname(self.output_file)
            try:
                if os.name == 'nt':
                    os.startfile(output_dir)
                elif os.name == 'posix':
                    import subprocess
                    subprocess.Popen(['xdg-open', output_dir])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")
        self.accept()

# --------------------------------------------------
# SuspendDialog Class
# Dialog for system suspend confirmation with countdown
# --------------------------------------------------
class SuspendDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.countdown = 60  
        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        self.setWindowTitle("System Suspend")
        self.setFixedSize(450, 240)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        icon_layout = QHBoxLayout()
        icon_label = QLabel()
        try:
            icon = qta.icon('fa5s.moon', color='#3498db')
            pixmap = icon.pixmap(36, 36)
            icon_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setFixedSize(36, 36)
            icon_label.setText("🌙")
            icon_label.setStyleSheet("font-size: 24px; color: #3498db;")

        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()

        layout.addLayout(icon_layout)

        self.message_label = QLabel(f"System will suspend in {self.countdown} seconds.")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e;")
        layout.addWidget(self.message_label)

        warning_label = QLabel("Please save all your work. The system will enter sleep mode.")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        layout.addSpacing(10)

        self.countdown_label = QLabel(f"00:{self.countdown:02d}")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #3498db;
            font-family: monospace;
        """)
        layout.addWidget(self.countdown_label)

        layout.addSpacing(15)

        button_layout = QHBoxLayout()

        self.cancel_btn = IconButton('fa5s.times', ' Cancel Suspend')
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFixedSize(140, 36)

        self.suspend_now_btn = IconButton('fa5s.bolt', ' Suspend Now')
        self.suspend_now_btn.clicked.connect(self.accept)
        self.suspend_now_btn.setFixedSize(140, 36)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.suspend_now_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

    def update_countdown(self):
        self.countdown -= 1
        self.message_label.setText(f"System will suspend in {self.countdown} seconds.")
        
        minutes = self.countdown // 60
        seconds = self.countdown % 60
        self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        if self.countdown <= 0:
            self.timer.stop()
            self.accept()

    def reject(self):
        self.timer.stop()
        super().reject()

    def accept(self):
        self.timer.stop()
        super().accept()

# --------------------------------------------------
# ShutdownDialog Class
# Dialog for system shutdown confirmation with countdown
# --------------------------------------------------
class ShutdownDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.countdown = 60
        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        self.setWindowTitle("System Shutdown")
        self.setFixedSize(450, 240)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        icon_layout = QHBoxLayout()
        icon_label = QLabel()
        try:
            icon = qta.icon('fa5s.power-off', color='#e74c3c')
            pixmap = icon.pixmap(36, 36)
            icon_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setFixedSize(36, 36)
            icon_label.setText("⏻")
            icon_label.setStyleSheet("font-size: 24px; color: #e74c3c;")

        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()

        layout.addLayout(icon_layout)

        self.message_label = QLabel(f"System will shutdown in {self.countdown} seconds.")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e;")
        layout.addWidget(self.message_label)

        warning_label = QLabel("Please save all your work. This action cannot be undone.")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        layout.addSpacing(10)

        self.countdown_label = QLabel(f"00:{self.countdown:02d}")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #e74c3c;
            font-family: monospace;
        """)
        layout.addWidget(self.countdown_label)

        layout.addSpacing(15)

        button_layout = QHBoxLayout()

        self.cancel_btn = IconButton('fa5s.times', ' Cancel Shutdown.')
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFixedSize(140, 36)

        self.shutdown_now_btn = IconButton('fa5s.bolt', ' Shutdown Now')
        self.shutdown_now_btn.clicked.connect(self.accept)
        self.shutdown_now_btn.setFixedSize(140, 36)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.shutdown_now_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

    def update_countdown(self):
        self.countdown -= 1
        self.message_label.setText(f"System will shutdown in {self.countdown} seconds.")
        
        minutes = self.countdown // 60
        seconds = self.countdown % 60
        self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        if self.countdown <= 0:
            self.timer.stop()
            self.accept()

    def reject(self):
        self.timer.stop()
        super().reject()

    def accept(self):
        self.timer.stop()
        super().accept()

# --------------------------------------------------
# AbortConfirmationDialog Class
# Dialog for confirming export abortion
# --------------------------------------------------
class AbortConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Abort Export")
        self.setFixedSize(450, 240)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        icon_layout = QHBoxLayout()
        icon_label = QLabel()
        try:
            icon = qta.icon('fa5s.exclamation-triangle', color='#f39c12')
            pixmap = icon.pixmap(36, 36)
            icon_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setFixedSize(36, 36)
            icon_label.setText("⚠")
            icon_label.setStyleSheet("font-size: 24px; color: #f39c12;")

        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()

        layout.addLayout(icon_layout)

        message_label = QLabel("Are you sure you want to abort the current export?")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        warning_label = QLabel("This action cannot be undone. The current progress will be lost.")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        layout.addSpacing(25)

        button_layout = QHBoxLayout()

        self.cancel_btn = IconButton('fa5s.times', ' Cancel')
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFixedSize(120, 36)

        self.abort_btn = IconButton('fa5s.stop', ' Abort Export')
        self.abort_btn.clicked.connect(self.accept)
        self.abort_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        self.abort_btn.setFixedSize(140, 36)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.abort_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        self.setLayout(layout)

# --------------------------------------------------
# VideoEditor Class
# Main application window
# --------------------------------------------------
class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.is_playing = False
        self.video_duration = 0
        self.start_time = 0
        self.end_time = 0
        self.last_output_file = None
        self.is_exporting = False
        self.background_timer = None
        self.current_playback_position = 0

        self.settings_manager = SettingsManager()
        self.video_processor = VideoProcessor()
        self.video_transformer = VideoTransformer()
        self.settings = self.settings_manager.load_settings()

        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)
        self.playback_timer.setInterval(50)

        self.export_start_time = None
        self.export_timer = QTimer()
        self.export_timer.timeout.connect(self.update_export_time)
        self.export_timer.setInterval(1000)

        self.export_status = "idle"
        self.init_ui()
        self.setup_core_connections()

        self.update_format_display()
        self.check_command_line_args()

        self._reset_crop_state()
        self.update_time_spinboxes_sync()

    # --------------------------------------------------
    # UI Initialization
    # --------------------------------------------------
    def init_ui(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setFixedSize(1000, 700)
        self.setAcceptDrops(True)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        content_splitter = QSplitter(Qt.Horizontal)
        left_panel = self.create_video_panel()
        right_panel = self.create_controls_panel()
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([600, 300])
        main_layout.addWidget(content_splitter, 1)

        time_layout = self.create_time_inputs()
        main_layout.addLayout(time_layout)

        progress_layout = self.create_progress_section()
        main_layout.addLayout(progress_layout)

        central_widget.setLayout(main_layout)

    def create_header(self):
        layout = QHBoxLayout()
        self.file_btn = IconButton('fa5s.folder-open', ' Select Video File')
        self.file_btn.clicked.connect(self.open_file)
        layout.addWidget(self.file_btn)

        self.video_info = QLabel("No video loaded")
        self.video_info.setAlignment(Qt.AlignCenter)
        self.video_info.setStyleSheet("font-size: 14px; color: #666666;")
        layout.addWidget(self.video_info, 1)

        self.about_btn = IconButton('fa5s.info-circle', ' About')
        self.about_btn.clicked.connect(self.show_about)
        layout.addWidget(self.about_btn)
        return layout

    def create_video_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.video_widget = VideoPlayer(self)
        self.video_widget.fileDropped.connect(self.load_video_file)
        layout.addWidget(self.video_widget, 1)

        controls_layout = self.create_video_controls()
        layout.addLayout(controls_layout)
        panel.setLayout(layout)
        return panel

    def create_video_controls(self):
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(3)

        self.fine_minus_btn = IconButton('fa5s.backward', ' -0.1s')
        self.minus_btn = IconButton('fa5s.step-backward', ' -1s')
        self.play_btn = IconButton('fa5s.play', ' Play')
        self.plus_btn = IconButton('fa5s.step-forward', ' +1s')
        self.fine_plus_btn = IconButton('fa5s.forward', ' +0.1s')
        self.set_in_btn = IconButton('fa5s.map-marker-alt', ' In ')
        self.set_out_btn = IconButton('fa5s.map-marker-alt', ' Out')

        self.fine_minus_btn.clicked.connect(lambda: self.seek_video(-0.1))
        self.minus_btn.clicked.connect(lambda: self.seek_video(-1))
        self.play_btn.clicked.connect(self.toggle_play)
        self.plus_btn.clicked.connect(lambda: self.seek_video(1))
        self.fine_plus_btn.clicked.connect(lambda: self.seek_video(0.1))
        self.set_in_btn.clicked.connect(self.set_in_point)
        self.set_out_btn.clicked.connect(self.set_out_point)

        for btn in [self.fine_minus_btn, self.minus_btn, self.play_btn,
                    self.plus_btn, self.fine_plus_btn, self.set_in_btn, self.set_out_btn]:
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)

        seek_layout = QVBoxLayout()
        self.seek_slider = CustomSlider(Qt.Horizontal)
        self.seek_slider.sliderMoved.connect(self.set_position)
        self.seek_slider.sliderPressed.connect(self.pause_video)
        
        self.seek_slider.setFixedHeight(24)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbbbbb;
                height: 12px;
                background: #e0e0e0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #3f8e93;
                width: 18px;
                margin: -4px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #3f8e93;
                border-radius: 6px;
            }
        """)
        
        seek_layout.addWidget(self.seek_slider)

        self.time_label = QLabel("00:00:00.000 / 00:00:00.000")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 11px; color: #666666;")
        seek_layout.addWidget(self.time_label)
        layout.addLayout(seek_layout)
        return layout

    def create_controls_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        edit_group = QGroupBox("Edit Controls")
        edit_layout = QGridLayout()
        edit_layout.setSpacing(5)

        self.rotate_left_btn = IconButton('fa5s.undo', ' 90° Left')
        self.rotate_right_btn = IconButton('fa5s.redo', ' 90° Right')
        self.flip_h_btn = IconButton('fa5s.arrows-alt-h', ' Flip H')
        self.flip_v_btn = IconButton('fa5s.arrows-alt-v', ' Flip V')
        self.reset_btn = IconButton('fa5s.sync', ' Reset All')
        self.crop_btn = IconButton('fa5s.crop', ' Crop Mode')

        self.crop_preset = QComboBox()
        self.crop_preset.addItems([
            "Free",
            "1:1 (Square)",
            "16:9 (Widescreen)",
            "9:16 (Portrait)",
            "4:3 (Standard)"
        ])
        self.crop_preset.currentIndexChanged.connect(self.apply_crop_preset)

        self.rotate_left_btn.clicked.connect(self.rotate_left)
        self.rotate_right_btn.clicked.connect(self.rotate_right)
        self.flip_h_btn.clicked.connect(self.flip_horizontal)
        self.flip_v_btn.clicked.connect(self.flip_vertical)
        self.reset_btn.clicked.connect(self.reset_transformations)
        self.crop_btn.clicked.connect(self.toggle_crop)

        edit_layout.addWidget(self.rotate_left_btn, 0, 0)
        edit_layout.addWidget(self.rotate_right_btn, 0, 1)
        edit_layout.addWidget(self.flip_h_btn, 1, 0)
        edit_layout.addWidget(self.flip_v_btn, 1, 1)
        edit_layout.addWidget(self.reset_btn, 2, 0, 1, 2)
        edit_layout.addWidget(self.crop_btn, 3, 0, 1, 2)
        edit_layout.addWidget(self.crop_preset, 4, 0, 1, 2)

        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)

        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_label = QLabel("Original - Copy")
        self.format_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        format_layout.addWidget(self.format_label, 1)

        self.settings_btn = IconButton('fa5s.cog', '')
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setToolTip("Advanced Settings")
        self.settings_btn.clicked.connect(self.show_advanced_settings)
        format_layout.addWidget(self.settings_btn)
        output_layout.addLayout(format_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        action_group = QGroupBox("Action after completion")
        action_layout = QVBoxLayout()
        self.action_combo = QComboBox()
        self.action_combo.addItems([
            "Show Completion Message",
            "Open Output Folder",
            "Close Application",
            "Suspend System",
            "Shutdown System"
        ])
        action_layout.addWidget(self.action_combo)
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        btn_layout = QHBoxLayout()
        self.export_btn = IconButton('fa5s.download', ' Export Video')
        self.quit_btn = IconButton('fa5s.sign-out-alt', ' Quit')

        self.export_btn.setFixedSize(130, 40)
        self.quit_btn.setFixedSize(130, 40)

        self.export_btn.clicked.connect(self.toggle_export)
        self.quit_btn.clicked.connect(self.quit_app)

        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.quit_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def create_time_inputs(self):
        layout = QHBoxLayout()

        start_group = QGroupBox("Start Time")
        start_layout = QHBoxLayout()
        self.start_h = QSpinBox(); self.start_h.setRange(0, 99)
        self.start_m = QSpinBox(); self.start_m.setRange(0, 59)
        self.start_s = QSpinBox(); self.start_s.setRange(0, 59)
        self.start_ms = QSpinBox(); self.start_ms.setRange(0, 999)

        start_layout.addWidget(QLabel("H:")); start_layout.addWidget(self.start_h)
        start_layout.addWidget(QLabel("M:")); start_layout.addWidget(self.start_m)
        start_layout.addWidget(QLabel("S:")); start_layout.addWidget(self.start_s)
        start_layout.addWidget(QLabel("MS:")); start_layout.addWidget(self.start_ms)
        start_group.setLayout(start_layout)
        layout.addWidget(start_group)

        end_group = QGroupBox("End Time")
        end_layout = QHBoxLayout()
        self.end_h = QSpinBox(); self.end_h.setRange(0, 99)
        self.end_m = QSpinBox(); self.end_m.setRange(0, 59)
        self.end_s = QSpinBox(); self.end_s.setRange(0, 59)
        self.end_ms = QSpinBox(); self.end_ms.setRange(0, 999)

        end_layout.addWidget(QLabel("H:")); end_layout.addWidget(self.end_h)
        end_layout.addWidget(QLabel("M:")); end_layout.addWidget(self.end_m)
        end_layout.addWidget(QLabel("S:")); end_layout.addWidget(self.end_s)
        end_layout.addWidget(QLabel("MS:")); end_layout.addWidget(self.end_ms)
        end_group.setLayout(end_layout)
        layout.addWidget(end_group)
        
        self.start_h.valueChanged.connect(self.on_time_spinboxes_changed)
        self.start_m.valueChanged.connect(self.on_time_spinboxes_changed)
        self.start_s.valueChanged.connect(self.on_time_spinboxes_changed)
        self.start_ms.valueChanged.connect(self.on_time_spinboxes_changed)
        
        self.end_h.valueChanged.connect(self.on_time_spinboxes_changed)
        self.end_m.valueChanged.connect(self.on_time_spinboxes_changed)
        self.end_s.valueChanged.connect(self.on_time_spinboxes_changed)
        self.end_ms.valueChanged.connect(self.on_time_spinboxes_changed)
        
        return layout

    def create_progress_section(self):
        layout = QVBoxLayout()
        
        progress_container = QWidget()
        progress_container.setFixedHeight(50)
        container_layout = QVBoxLayout(progress_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        progress_info_layout = QHBoxLayout()
        
        self.progress_percent = QLabel("Ready")
        self.progress_percent.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #666666;
                min-width: 60px;
            }
        """)
        
        self.progress_status = QLabel("No active operation")
        self.progress_status.setStyleSheet("color: #666666;")
        
        self.progress_time_label = QLabel("")
        self.progress_time_label.setStyleSheet("""
            QLabel {
                color: #666666;
                min-width: 100px;
            }
        """)
        
        progress_info_layout.addWidget(self.progress_percent)
        progress_info_layout.addStretch()
        progress_info_layout.addWidget(self.progress_status)
        progress_info_layout.addWidget(self.progress_time_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        
        self.set_progress_bar_style(active=False)
        
        container_layout.addLayout(progress_info_layout)
        container_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container)
        return layout
    
    def set_progress_bar_style(self, active=True):
        if active:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3f8e93;
                    border-radius: 5px;
                    text-align: center;
                    font-weight: bold;
                    background-color: #f5f5f5;
                }
                QProgressBar::chunk {
                    background-color: #3f8e93;
                    border-radius: 4px;
                }
            """)
        else:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    text-align: center;
                    font-weight: normal;
                    color: #999999;
                    background-color: #f5f5f5;
                }
                QProgressBar::chunk {
                    background-color: #e0e0e0;
                    border-radius: 4px;
                }
            """)

    # --------------------------------------------------
    # Core Connections Setup
    # --------------------------------------------------
    def setup_core_connections(self):
        self.video_processor.progress_updated.connect(self.update_progress)
        self.video_processor.export_finished.connect(self.export_complete)
        self.video_processor.export_started.connect(self.export_started)

    # --------------------------------------------------
    # Video Loading and Time Management
    # --------------------------------------------------
    def on_video_loaded(self):
        if self.video_path:
            QTimer.singleShot(300, lambda: self.video_widget.get_video_widget().fit_video_in_view())

            if self.video_duration > 0:
                self.start_time = 0
                self.end_time = self.video_duration
                self.update_time_inputs(0, 'start')
                self.update_time_inputs(self.video_duration, 'end')
                self.seek_slider.set_time_range(self.start_time, self.end_time, self.video_duration)

    def update_time_spinboxes_sync(self):
        if not self.video_path:
            return
            
        self.start_h.blockSignals(True)
        self.start_m.blockSignals(True)
        self.start_s.blockSignals(True)
        self.start_ms.blockSignals(True)
        self.end_h.blockSignals(True)
        self.end_m.blockSignals(True)
        self.end_s.blockSignals(True)
        self.end_ms.blockSignals(False)
        
        self.start_h.setValue(0)
        self.start_m.setValue(0)
        self.start_s.setValue(0)
        self.start_ms.setValue(0)
        
        duration_seconds = self.video_duration / 1000
        h, m, s, ms = seconds_to_hmsms(duration_seconds)
        self.end_h.setValue(h)
        self.end_m.setValue(m)
        self.end_s.setValue(s)
        self.end_ms.setValue(ms)
        
        self.start_h.blockSignals(False)
        self.start_m.blockSignals(False)
        self.start_s.blockSignals(False)
        self.start_ms.blockSignals(False)
        self.end_h.blockSignals(False)
        self.end_m.blockSignals(False)
        self.end_s.blockSignals(False)
        self.end_ms.blockSignals(False)

    def on_time_spinboxes_changed(self):
        if not self.video_path:
            return
        
        start_h = self.start_h.value()
        start_m = self.start_m.value()
        start_s = self.start_s.value()
        start_ms = self.start_ms.value()
        
        end_h = self.end_h.value()
        end_m = self.end_m.value()
        end_s = self.end_s.value()
        end_ms = self.end_ms.value()
        
        start_seconds = hmsms_to_seconds(start_h, start_m, start_s, start_ms)
        end_seconds = hmsms_to_seconds(end_h, end_m, end_s, end_ms)
        
        self.start_time = start_seconds * 1000
        self.end_time = end_seconds * 1000
        
        if self.start_time > self.video_duration:
            self.start_time = self.video_duration
            self.update_time_inputs(self.start_time, 'start')
        if self.end_time > self.video_duration:
            self.end_time = self.video_duration
            self.update_time_inputs(self.end_time, 'end')
        
        self.seek_slider.set_time_range(self.start_time, self.end_time, self.video_duration)
        self.show_notification(f"Time range updated: {hmsms_str_from_ms(self.start_time)} to {hmsms_str_from_ms(self.end_time)}")

    def update_crop_button_state(self):
        if not hasattr(self, 'crop_btn'):
            return
            
        if not self.video_path:
            self.crop_btn.setEnabled(False)
            return
            
        if hasattr(self.video_transformer, 'current_rotation'):
            if self.video_transformer.current_rotation != 0:
                self.crop_btn.setEnabled(False)
                if hasattr(self, 'crop_btn') and self.crop_btn.styleSheet():
                    self.crop_btn.setStyleSheet("")
            else:
                self.crop_btn.setEnabled(True)

    def _reset_crop_state(self):
        if not hasattr(self, "video_widget"):
            return

        video_player = self.video_widget.get_video_widget()

        try:
            if getattr(video_player, "crop_mode", False):
                video_player.toggle_crop_mode()
        except Exception:
            pass

        try:
            video_player.set_crop_aspect_ratio(0, 0)
        except Exception:
            pass

        if hasattr(self, "video_transformer") and self.video_transformer:
            self.video_transformer.crop_rect = None
            self.video_transformer.crop_mode = False

        if hasattr(self, "crop_btn") and self.crop_btn:
            self.crop_btn.setStyleSheet("")
            self.update_crop_button_state()
            
        if hasattr(self, "crop_preset") and self.crop_preset:
            self.crop_preset.blockSignals(True)
            self.crop_preset.setCurrentIndex(0)
            self.crop_preset.blockSignals(False)

    # --------------------------------------------------
    # File Operations
    # --------------------------------------------------
    def load_video_file(self, file_path):
        if file_path and os.path.exists(file_path):
            self._reset_crop_state()

            self.video_transformer = VideoTransformer()
            self.video_path = file_path

            success = self.video_widget.load_video(file_path)
            if not success:
                self.show_notification("Error loading video file")
                return

            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                if fps > 0:
                    self.video_duration = frame_count / fps * 1000
                else:
                    self.video_duration = get_video_duration(file_path) * 1000

                cap.release()
            else:
                self.video_duration = get_video_duration(file_path) * 1000

            file_size = os.path.getsize(file_path)
            size_str = format_file_size(file_size)
            video_info = get_video_info(file_path)

            info_text = f"{os.path.basename(file_path)} ({size_str})"
            if self.video_duration > 0:
                duration_str = hmsms_str_from_ms(self.video_duration)
                info_text += f" - {duration_str}"
            if video_info.get('width') and video_info.get('height'):
                info_text += f" - {video_info['width']}x{video_info['height']}"
            
            if video_info.get('codec'):
                info_text += f" - {video_info['codec']}"
            elif video_info.get('video_codec'):
                info_text += f" - {video_info['video_codec']}"

            self.video_info.setText(info_text)

            self.start_time = 0
            self.end_time = self.video_duration
            self.update_time_inputs(0, 'start')
            self.update_time_inputs(self.video_duration, 'end')

            self.seek_slider.setRange(0, int(self.video_duration))
            self.seek_slider.set_time_range(self.start_time, self.end_time, self.video_duration)
            self.seek_slider.setValue(0)

            QTimer.singleShot(500, lambda: self.video_widget.get_video_widget().fit_video_in_view())

            self.show_notification(f"Loaded: {os.path.basename(file_path)}")
            self.update_crop_button_state()
            self.update_time_spinboxes_sync()

    def open_file(self):
        if self.is_exporting:
            self.show_notification("Please wait for current export to finish")
            return

        options = QFileDialog.Options()
        home_dir = os.path.expanduser("~")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", home_dir,
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp *.ogg);;All Files (*)",
            options=options
        )
        if file_path:
            self.load_video_file(file_path)

    def check_command_line_args(self):
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path) and is_video_file(file_path):
                QTimer.singleShot(100, lambda: self.load_video_file(file_path))

    # --------------------------------------------------
    # Drag and Drop Events
    # --------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if self.is_exporting:
            return

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and is_video_file(urls[0].toLocalFile()):
                event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if self.is_exporting:
            return

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and is_video_file(urls[0].toLocalFile()):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if self.is_exporting:
            self.show_notification("Cannot load video during export")
            return

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if is_video_file(file_path):
                    self.load_video_file(file_path)
                    event.acceptProposedAction()

    # --------------------------------------------------
    # Video Playback Controls
    # --------------------------------------------------
    def toggle_play(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return

        if self.is_playing:
            self.video_widget.pause()
            self.is_playing = False
            self.play_btn.setIcon(qta.icon('fa5s.play'))
            self.play_btn.setText(" Play")
            self.playback_timer.stop()
        else:
            self.video_widget.play()
            self.is_playing = True
            self.play_btn.setIcon(qta.icon('fa5s.pause'))
            self.play_btn.setText(" Pause")
            self.playback_timer.start()

    def pause_video(self):
        if self.is_playing:
            self.toggle_play()

    def seek_video(self, seconds):
        if not self.video_path:
            return

        current_time = self.video_widget.get_current_time() * 1000
        new_time = current_time + (seconds * 1000)
        new_time = max(0, min(new_time, self.video_duration))

        self.video_widget.set_position(int(new_time))
        self.seek_slider.setValue(int(new_time))
        self.current_playback_position = int(new_time)
        self.update_time_display()

    def set_position(self, position):
        self.current_playback_position = position
        self.video_widget.set_position(position)
        self.update_time_display()

    def update_playback_position(self):
        if self.is_playing and self.video_path:
            current_time = self.video_widget.get_current_time() * 1000
            self.seek_slider.setValue(int(current_time))
            self.current_playback_position = int(current_time)
            self.update_time_display()

    def update_time_display(self):
        if not self.video_path:
            return

        current_time = self.seek_slider.value()
        current_str = hmsms_str_from_ms(current_time)
        duration_str = hmsms_str_from_ms(self.video_duration)
        self.time_label.setText(f"{current_str} / {duration_str}")

    def set_in_point(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return

        position = self.seek_slider.value()
        self.start_time = position
        self.update_time_inputs(position, 'start')
        self.seek_slider.set_time_range(self.start_time, self.end_time, self.video_duration)
        self.show_notification(f"In point set to {hmsms_str_from_ms(position)}")

    def set_out_point(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return

        position = self.seek_slider.value()
        self.end_time = position
        self.update_time_inputs(position, 'end')
        self.seek_slider.set_time_range(self.start_time, self.end_time, self.video_duration)
        self.show_notification(f"Out point set to {hmsms_str_from_ms(position)}")

    def update_time_inputs(self, milliseconds, time_type):
        h, m, s, ms = milliseconds_to_hmsms(milliseconds)

        if time_type == 'start':
            self.start_h.setValue(h)
            self.start_m.setValue(m)
            self.start_s.setValue(s)
            self.start_ms.setValue(ms)
        else:
            self.end_h.setValue(h)
            self.end_m.setValue(m)
            self.end_s.setValue(s)
            self.end_ms.setValue(ms)

    # --------------------------------------------------
    # Video Transformation Operations
    # --------------------------------------------------
    def rotate_left(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return

        self._reset_crop_state()

        try:
            self.video_widget.rotate_left()
            self.video_transformer.rotate_video("left")
            self.show_notification("Rotated 90° left")
            self.update_crop_button_state()
        except Exception as e:
            self.show_notification(f"Rotation error: {str(e)}")

    def rotate_right(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return

        self._reset_crop_state()

        try:
            self.video_widget.rotate_right()
            self.video_transformer.rotate_video("right")
            self.show_notification("Rotated 90° right")
            self.update_crop_button_state()
        except Exception as e:
            self.show_notification(f"Rotation error: {str(e)}")

    def flip_horizontal(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return

        self._reset_crop_state()

        try:
            self.video_widget.flip_horizontal()
            self.video_transformer.rotate_video("horizontal")
            self.show_notification("Flipped horizontally")
        except Exception as e:
            self.show_notification(f"Flip error: {str(e)}")

    def flip_vertical(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return

        self._reset_crop_state()

        try:
            self.video_widget.flip_vertical()
            self.video_transformer.rotate_video("vertical")
            self.show_notification("Flipped vertically")
        except Exception as e:
            self.show_notification(f"Flip error: {str(e)}")

    def reset_transformations(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return

        try:
            self.video_widget.reset_transformations()
            self.video_transformer.rotate_video("reset")
            self._reset_crop_state()
            QTimer.singleShot(100, lambda: self.video_widget.get_video_widget().fit_video_in_view())
            self.show_notification("All transformations reset")
            self.update_crop_button_state()
        except Exception as e:
            self.show_notification(f"Reset error: {str(e)}")

    def toggle_crop(self):
        if not self.video_path:
            self.show_notification("Please load a video file first")
            return
        
        if self.video_transformer and hasattr(self.video_transformer, 'current_rotation'):
            if self.video_transformer.current_rotation != 0:
                self.show_notification("Crop is not available while video is rotated. Please reset rotation first.")
                return

        try:
            crop_mode = self.video_widget.toggle_crop_mode()
            
            self.video_transformer.crop_mode = crop_mode
            
            if crop_mode:
                video_player = self.video_widget.get_video_widget()
                if hasattr(video_player, 'get_current_crop_rect'):
                    current_crop = video_player.get_current_crop_rect()
                    if current_crop:
                        self.video_transformer.crop_rect = current_crop
                
                self.show_notification("Crop mode activated")
                self.crop_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                QTimer.singleShot(
                    100,
                    lambda: self.video_widget.get_video_widget()._update_crop_overlay_bounds()
                )
            else:
                self.video_transformer.crop_rect = None
                self.show_notification("Crop mode deactivated")
                self.crop_btn.setStyleSheet("")
        except Exception as e:
            self.show_notification(f"Crop error: {str(e)}")

    def apply_crop_preset(self):
        if not self.video_path:
            return

        preset = self.crop_preset.currentText()
        video_player = self.video_widget.get_video_widget()

        if not hasattr(video_player, 'crop_mode') or not video_player.crop_mode:
            return

        if preset == "Free":
            video_player.set_crop_aspect_ratio(0, 0)
            self.show_notification("Free crop mode")
        elif preset == "1:1 (Square)":
            video_player.set_crop_aspect_ratio(1, 1)
            self.show_notification("1:1 square crop")
        elif preset == "16:9 (Widescreen)":
            video_player.set_crop_aspect_ratio(16, 9)
            self.show_notification("16:9 widescreen crop")
        elif preset == "9:16 (Portrait)":
            video_player.set_crop_aspect_ratio(9, 16)
            self.show_notification("9:16 portrait crop")
        elif preset == "4:3 (Standard)":
            video_player.set_crop_aspect_ratio(4, 3)
            self.show_notification("4:3 standard crop")

    # --------------------------------------------------
    # Settings and Dialogs
    # --------------------------------------------------
    def show_advanced_settings(self):
        if self.is_exporting:
            self.show_notification("Cannot change settings during export")
            return

        dialog = AdvancedSettingsDialog(self, self.settings)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = dialog.get_updated_settings()
            if self.settings_manager.save_settings(self.settings):
                self.update_format_display()
                self.show_notification("Settings saved successfully")
            else:
                self.show_notification("Error saving settings")

    def update_format_display(self):
        audio_output = self.settings.get("audio_output_format", "none")
        if audio_output != "none":
            format_name = audio_output.upper()
            self.format_label.setText(f"AUDIO ONLY - {format_name}")
            self.format_label.setStyleSheet("font-weight: bold; color: #e67e22;")
        else:
            format_index = self.settings.get("format_index", 0)
            if format_index == 0:
                self.format_label.setText("Original - Copy (fastest)")
                self.format_label.setStyleSheet("font-weight: bold; color: #27ae60;")
            else:
                formats = ["Original - Copy", "MP4", "MKV", "WEBM"]
                format_text = formats[format_index] if format_index < len(formats) else "MP4"
                format_name = format_text.split(" - ")[0]

                video_codec = self.settings.get("video_codec", "H264")
                if video_codec == "Original":
                    video_codec = "Same as input"

                quality = self.settings.get("quality", "1080p")
                if quality == "Original":
                    quality = "Same as input"

                self.format_label.setText(f"{format_name} - {video_codec} - {quality}")
                self.format_label.setStyleSheet("font-weight: bold; color: #2980b9;")

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()

    # --------------------------------------------------
    # Export Operations
    # --------------------------------------------------
    def toggle_export(self):
        if not self.is_exporting:
            self.start_export()
        else:
            self.show_abort_confirmation()

    def export_started(self):
        self.export_status = "exporting"
        self.progress_status.setText("Exporting...")
        self.progress_status.setStyleSheet("color: #3f8e93; font-weight: bold;")
        self.progress_percent.setStyleSheet("font-weight: bold; color: #3f8e93;")
        
        self.set_progress_bar_style(active=True)
        
        self.export_start_time = time.time()
        self.export_timer.start()
        self.update_export_time()

    def update_export_time(self):
        if self.export_start_time is None:
            return
        elapsed = time.time() - self.export_start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.progress_time_label.setText(f"⏱ {time_str}")

    def start_export(self):
        if not self.video_path:
            self.show_notification("Please select a video file first")
            return

        if self.video_processor.is_processing:
            self.show_notification("Export already in progress")
            return

        if self.is_playing:
            self.video_widget.pause()
            self.is_playing = False
            self.play_btn.setIcon(qta.icon('fa5s.play'))
            self.play_btn.setText(" Play")
            self.playback_timer.stop()
        
        self.is_exporting = True
        self.export_btn.setIcon(qta.icon('fa5s.stop'))
        self.export_btn.setText(" Abort Export")
        self.export_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        self.export_btn.setFixedSize(130, 40)
        self.progress_status.setText("Initializing...")

        QApplication.processEvents()

        if self.start_time == 0 and self.end_time == 0:
            self.start_time = 0
            self.end_time = self.video_duration
            self.update_time_inputs(0, 'start')
            self.update_time_inputs(self.video_duration, 'end')

        start_time = hmsms_to_seconds(
            self.start_h.value(), self.start_m.value(),
            self.start_s.value(), self.start_ms.value()
        )
        end_time = hmsms_to_seconds(
            self.end_h.value(), self.end_m.value(),
            self.end_s.value(), self.end_ms.value()
        )

        if start_time >= end_time:
            self.show_notification("Start time must be before end time")
            self.is_exporting = False
            self.export_btn.setIcon(qta.icon('fa5s.download'))
            self.export_btn.setText(" Export Video")
            self.export_btn.setStyleSheet("")
            self.export_btn.setFixedSize(130, 40)
            return

        if end_time > self.video_duration / 1000:
            self.show_notification("End time exceeds video duration")
            self.is_exporting = False
            self.export_btn.setIcon(qta.icon('fa5s.download'))
            self.export_btn.setText(" Export Video")
            self.export_btn.setStyleSheet("")
            self.export_btn.setFixedSize(130, 40)
            return

        input_name = os.path.splitext(os.path.basename(self.video_path))[0]
        input_name = sanitize_filename(input_name)
        audio_output = self.settings.get("audio_output_format", "none")

        video_player = self.video_widget.get_video_widget()
        
        if video_player.crop_mode:
            video_player._update_crop_overlay_bounds()
        
        self.video_transformer.sync_with_player(video_player)
        
        video_filters = self.video_transformer.build_video_filter_for_ffmpeg()

        print(f"\n=== EXPORT DEBUG INFO ===")
        print(f"Crop mode: {self.video_transformer.crop_mode}")
        print(f"Crop rect: {self.video_transformer.crop_rect}")
        print(f"Rotation: {self.video_transformer.current_rotation}°")
        print(f"Flip H: {self.video_transformer.flip_horizontal}")
        print(f"Flip V: {self.video_transformer.flip_vertical}")
        print(f"Video filters: {video_filters}")
        print(f"========================")

        if audio_output != "none":
            if audio_output == "flac":
                ext = ".flac"
            elif audio_output == "aac":
                ext = ".m4a"
            else:
                ext = ".mp3"

            output_file = unique_output_path(input_name, ext, audio_output)
            self.last_output_file = output_file

            success = self.video_processor.export_audio(
                self.video_path, output_file, self.settings, start_time, end_time
            )

            if not success:
                self.show_notification("Failed to start audio export")
                self.is_exporting = False
                self.export_btn.setIcon(qta.icon('fa5s.download'))
                self.export_btn.setText(" Export Video")
                self.export_btn.setStyleSheet("")
                self.export_btn.setFixedSize(130, 40)
        else:
            format_index = self.settings.get("format_index", 0)

            if format_index == 0:
                original_ext = os.path.splitext(self.video_path)[1]
                base_name = input_name
                output_file = unique_output_path(base_name, original_ext, "original")
                self.last_output_file = output_file
                self.settings["input_path"] = self.video_path
            else:
                video_codec = self.settings.get("video_codec", "H264")
                quality = self.settings.get("quality", "1080p")

                formats = ["Original - Copy", "MP4", "MKV", "WEBM"]
                format_text = formats[format_index] if format_index < len(formats) else "MP4"
                format_type = format_text.split(" - ")[0].lower()
                ext = f".{format_type}"
                base_name = input_name
                output_file = unique_output_path(base_name, ext, format_type)
                self.last_output_file = output_file

            success = self.video_processor.export_video(
                self.video_path, output_file, self.settings, start_time, end_time, video_filters
            )

            if not success:
                self.show_notification("Failed to start video export")
                self.is_exporting = False
                self.export_btn.setIcon(qta.icon('fa5s.download'))
                self.export_btn.setText(" Export Video")
                self.export_btn.setStyleSheet("")
                self.export_btn.setFixedSize(130, 40)

    def show_abort_confirmation(self):
        dialog = AbortConfirmationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.abort_export()

    def abort_export(self):
        if self.video_processor.is_processing:
            self.progress_status.setText("Aborting...")
            QApplication.processEvents()

            self.video_processor.abort_processing()

            QTimer.singleShot(100, self._check_abort_status)
        else:
            self.show_notification("No export in progress")
            self.is_exporting = False
            self.export_btn.setIcon(qta.icon('fa5s.download'))
            self.export_btn.setText(" Export Video")
            self.export_btn.setStyleSheet("")
            self.export_btn.setFixedSize(130, 40)

    def _check_abort_status(self):
        if self.video_processor.is_processing:
            QTimer.singleShot(100, self._check_abort_status)
        else:
            self.is_exporting = False
            self.progress_bar.setValue(0)
            self.progress_percent.setText("Ready")
            self.progress_status.setText("Export aborted")
            self.progress_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.progress_time_label.setText("✗ Aborted")
            self.progress_time_label.setStyleSheet("color: #e74c3c;")
            self.export_btn.setIcon(qta.icon('fa5s.download'))
            self.export_btn.setText(" Export Video")
            self.export_btn.setStyleSheet("")
            self.export_btn.setFixedSize(130, 40)
            self.show_notification("Export aborted by user")

    def update_progress(self, percent):
        self.progress_bar.setValue(percent)
        self.progress_percent.setText(f"{percent}%")

    def export_complete(self, output_file, success):
        print(f"Export complete: {output_file}, success: {success}")

        self.is_exporting = False
        self.export_timer.stop()

        self.progress_bar.setValue(0)
        self.progress_percent.setText("Ready")

        if success:
            self.export_status = "success"
            self.progress_status.setText("Export Done")
            self.progress_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            if self.export_start_time:
                elapsed = time.time() - self.export_start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.progress_time_label.setText(f"✓ {time_str}")
                self.progress_time_label.setStyleSheet("color: #27ae60;")
            
            self.set_progress_bar_style(active=False)
            
            action = self.action_combo.currentText()

            if "message" in action.lower():
                dialog = ExportCompleteDialog(self, output_file)
                dialog.exec_()
            elif "folder" in action.lower():
                if output_file and os.path.exists(output_file):
                    output_dir = os.path.dirname(output_file)
                    try:
                        if os.name == 'nt':
                            os.startfile(output_dir)
                        elif os.name == 'posix':
                            import subprocess
                            subprocess.Popen(['xdg-open', output_dir])
                        self.show_notification("Output folder opened")
                    except Exception as e:
                        self.show_notification(f"Error opening folder: {str(e)}")
            elif "close" in action.lower():
                self.close()
            elif "suspend" in action.lower():
                self.suspend_system()
            elif "shutdown" in action.lower():
                self.shutdown_system()
        else:
            self.export_status = "error"
            self.progress_status.setText("Export Failed")
            self.progress_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
            if self.export_start_time:
                elapsed = time.time() - self.export_start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.progress_time_label.setText(f"✗ {time_str}")
                self.progress_time_label.setStyleSheet("color: #e74c3c;")
            
            self.set_progress_bar_style(active=False)
            
            if output_file and "abort" not in self.progress_status.text():
                self.show_notification("Export failed - check console for details")
        
        self.export_btn.setIcon(qta.icon('fa5s.download'))
        self.export_btn.setText(" Export Video")
        self.export_btn.setStyleSheet("")
        self.export_btn.setFixedSize(130, 40)

    # --------------------------------------------------
    # System Operations
    # --------------------------------------------------
    def suspend_system(self):
        dialog = SuspendDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self._perform_suspend()
        else:
            self.show_notification("Suspend cancelled.")

    def _perform_suspend(self):
        self.show_notification("Finalizing files before suspend...")
        QApplication.processEvents()
        
        import time
        time.sleep(5)
        
        try:
            os.sync()
        except AttributeError:
            pass
        
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Linux":
                try:
                    subprocess.run(["systemctl", "suspend"], check=True)
                except:
                    subprocess.run(["pm-suspend"], check=True)
            elif system == "Darwin":
                subprocess.run(["pmset", "sleepnow"], check=True)
            elif system == "Windows":
                import ctypes
                ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
                
        except Exception as e:
            self.show_notification(f"Error suspending system: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not suspend system: {str(e)}")

    def shutdown_system(self):
        dialog = ShutdownDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self._perform_shutdown()
        else:
            self.show_notification("Shutdown cancelled.")

    def _perform_shutdown(self):
        self.show_notification("Finalizing files before shutdown...")
        QApplication.processEvents()
        
        import time
        time.sleep(5)
        
        try:
            os.sync()
        except AttributeError:
            pass
        
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Linux":
                try:
                    subprocess.run(["systemctl", "poweroff"], check=True)
                except:
                    subprocess.run(["shutdown", "-h", "now"], check=True)
            elif system == "Darwin":
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
            elif system == "Windows":
                subprocess.run(["shutdown", "/s", "/f", "/t", "5"], check=True)
                
        except Exception as e:
            self.show_notification(f"Error shutting down: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not shutdown system: {str(e)}")

    # --------------------------------------------------
    # Application Lifecycle
    # --------------------------------------------------
    def quit_app(self):
        print("quit_app called")

        self.pause_video()

        if self.video_processor.is_processing or self.is_exporting:
            print("Export in progress, showing dialog...")

            msg_box = QMessageBox()
            msg_box.setWindowTitle("Quit NamaCut")
            msg_box.setText("An export is in progress. Are you sure you want to quit?\n\nThe export will be aborted and incomplete file removed.")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)

            reply = msg_box.exec_()

            if reply == QMessageBox.Yes:
                print("User confirmed quit with export in progress")

                progress = self.progress_bar.value() if self.progress_bar.isVisible() else 0
                print(f"Export progress at quit: {progress}%")

                self.video_processor.abort_processing()

                import time
                start_time = time.time()

                while (self.video_processor.is_processing or self.is_exporting) and (time.time() - start_time) < 3:
                    print(f"Waiting for abort... ({time.time() - start_time:.1f}s)")
                    QApplication.processEvents()
                    time.sleep(0.1)

                if hasattr(self, 'video_widget'):
                    self.video_widget.stop()

                print("Closing application...")
                self.close()
            else:
                print("User cancelled quit")
        else:
            print("No export in progress, asking for confirmation...")

            msg_box = QMessageBox()
            msg_box.setWindowTitle("Quit NamaCut")
            msg_box.setText("Are you sure you want to quit?")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)

            reply = msg_box.exec_()

            if reply == QMessageBox.Yes:
                if hasattr(self, 'video_widget'):
                    self.video_widget.stop()

                print("Closing application...")
                self.close()

    def check_background_export(self):
        if not self.video_processor.is_processing and not self.is_exporting:
            print("Background export completed, closing application...")
            if self.background_timer:
                self.background_timer.stop()
            self.close()

    def closeEvent(self, event):
        print("closeEvent called")

        if hasattr(self, 'video_widget') and self.video_widget:
            print("Stopping video playback...")
            try:
                self.video_widget.stop()
            except Exception:
                pass

        if self.video_processor.is_processing or self.is_exporting:
            print("Export is in progress, showing confirmation dialog...")

            self.pause_video()

            msg_box = QMessageBox()
            msg_box.setWindowTitle("Export in Progress")
            msg_box.setText("An export is still in progress. Do you want to:\n\n1. Abort export and quit (Recommended)\n2. Continue export in background\n3. Cancel and stay in application")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Cancel)

            reply = msg_box.exec_()

            if reply == QDialog.Yes:
                print("User chose to abort export and quit")
                self.video_processor.abort_processing()

                QApplication.processEvents()

                import time
                start_time = time.time()
                max_wait = 5

                while (self.video_processor.is_processing or self.is_exporting) and (time.time() - start_time) < max_wait:
                    print(f"Waiting for export to stop... ({time.time() - start_time:.1f}s)")
                    QApplication.processEvents()
                    time.sleep(0.2)

                if self.video_processor.is_processing:
                    print("Warning: Export still in progress after waiting")

                print("Closing window...")
                event.accept()

            elif reply == QDialog.No:
                print("User chose to continue export in background")
                self.hide()
                event.ignore()

                self.background_timer = QTimer()
                self.background_timer.timeout.connect(self.check_background_export)
                self.background_timer.start(1000)

                self.show_notification("Export will continue in background. Application minimized.")

            else:
                print("User cancelled close")
                event.ignore()

        else:
            print("No export in progress, closing normally")
            event.accept()

    # --------------------------------------------------
    # Utility Methods
    # --------------------------------------------------
    def show_notification(self, message):
        self.statusBar().showMessage(f"{message}", 3000)