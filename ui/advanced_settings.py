# ============================================================
# AdvancedSettingsDialog Module
# This file contains the AdvancedSettingsDialog class
# ============================================================

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QWidget, QLabel, QComboBox, QSlider, QLineEdit,
                            QGroupBox, QDialogButtonBox, QGridLayout)
from PyQt5.QtCore import Qt
import qtawesome as qta

# --------------------------------------------------
# Class: AdvancedSettingsDialog
# Description: Advanced output settings dialog for video and audio configuration
# --------------------------------------------------
class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        """
        Constructor for AdvancedSettingsDialog
        
        Parameters:
            parent (QWidget, optional): Parent widget. Default: None
            settings (dict, optional): Current application settings. Default: None
        """
        super().__init__(parent)
        self.settings = settings or {}  # Store current settings
        
        # Dialog styling
        self.setStyleSheet("""
            QDialog {
                border: 2px solid #3f8e93;
                border-radius: 0px;
            }
        """)
        
        self.setup_ui()  # Initialize UI components
        self.load_current_settings()  # Load existing settings
        self.setup_connections()  # Connect signals to slots
        self.update_ui_state()  # Update UI based on current state
        
    # --------------------------------------------------
    # UI setup methods
    # --------------------------------------------------
    def setup_ui(self):
        """
        Setup the main UI layout including tabs and buttons
        """
        self.setWindowTitle("Output Settings")
        self.setMinimumSize(550, 650)
        
        layout = QVBoxLayout()
        
        # Tab widget for video/audio settings
        self.tab_widget = QTabWidget()
        
        self.video_tab = self.create_video_tab()  # Create video settings tab
        self.tab_widget.addTab(self.video_tab, "Video Export")
        
        self.audio_tab = self.create_audio_tab()  # Create audio settings tab
        self.tab_widget.addTab(self.audio_tab, "Audio Only Export")
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons (OK/Cancel)
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)  # OK button
        button_box.rejected.connect(self.reject)  # Cancel button
        
        layout.addWidget(button_box)
        self.setLayout(layout)
        
    def create_video_tab(self):
        """
        Create and configure the video settings tab
        
        Returns:
            QWidget: The video settings tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Video format group box
        format_group = QGroupBox("Video Format")
        format_layout = QGridLayout()
        format_layout.setSpacing(8)
        
        format_layout.addWidget(QLabel("Container:"), 0, 0)
        self.container_combo = QComboBox()
        self.container_combo.addItems(["Original - Copy", "MP4 (.mp4)", "Matroska (.mkv)", "WebM (.webm)"])
        format_layout.addWidget(self.container_combo, 0, 1)
        
        format_layout.addWidget(QLabel("Video Codec:"), 1, 0)
        self.video_codec_combo = QComboBox()
        self.video_codec_combo.addItems(["Original", "H.264 (libx264)", "H.265 (libx265)", "VP9 (libvpx-vp9)"])
        format_layout.addWidget(self.video_codec_combo, 1, 1)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Video quality group box
        self.quality_group = QGroupBox("Video Quality")
        quality_layout = QVBoxLayout()
        
        quality_slider_layout = QHBoxLayout()
        quality_slider_layout.addWidget(QLabel("Low"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 10)
        self.quality_slider.setValue(6)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(1)
        
        # Slider styling
        self.quality_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbbbbb;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #3f8e93;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #3f8e93;
                border-radius: 4px;
            }
        """)
        
        quality_slider_layout.addWidget(self.quality_slider)
        quality_slider_layout.addWidget(QLabel("High"))
        
        self.quality_value_label = QLabel("Quality: 6/10")
        self.quality_value_label.setAlignment(Qt.AlignCenter)
        self.quality_value_label.setStyleSheet("font-weight: bold;")
        
        self.crf_value_label = QLabel("CRF: 23")
        self.crf_value_label.setAlignment(Qt.AlignCenter)
        self.crf_value_label.setStyleSheet("color: #666666;")
        
        self.file_size_label = QLabel("Estimated file size: --")
        self.file_size_label.setAlignment(Qt.AlignCenter)
        self.file_size_label.setStyleSheet("color: #3498db; font-style: italic;")
        
        quality_layout.addLayout(quality_slider_layout)
        quality_layout.addWidget(self.quality_value_label)
        quality_layout.addWidget(self.crf_value_label)
        quality_layout.addWidget(self.file_size_label)
        
        self.quality_group.setLayout(quality_layout)
        layout.addWidget(self.quality_group)
        
        # Resolution group box
        self.resolution_group = QGroupBox("Output Resolution")
        resolution_layout = QVBoxLayout()
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "Original",
            "Ultra HD (3840x2160)",
            "QHD (2560x1440)",
            "Full HD 1080p (1920x1080)",
            "HD 720p (1280x720)",
            "SD 480p (854x480)"
        ])
        resolution_layout.addWidget(self.resolution_combo)
        self.resolution_group.setLayout(resolution_layout)
        layout.addWidget(self.resolution_group)
        
        # Audio settings group box (for video tab)
        self.audio_group = QGroupBox("Audio Settings")
        audio_layout = QVBoxLayout()
        
        audio_format_layout = QHBoxLayout()
        audio_format_layout.addWidget(QLabel("Audio Format:"))
        self.video_audio_format_combo = QComboBox()
        self.video_audio_format_combo.addItems(["Original", "AAC", "MP3"])
        audio_format_layout.addWidget(self.video_audio_format_combo)
        audio_layout.addLayout(audio_format_layout)
        
        audio_bitrate_layout = QHBoxLayout()
        audio_bitrate_layout.addWidget(QLabel("Audio Bitrate:"))
        self.video_audio_bitrate_combo = QComboBox()
        self.video_audio_bitrate_combo.addItems(["Original", "128 kbps", "192 kbps", "256 kbps", "320 kbps"])
        audio_bitrate_layout.addWidget(self.video_audio_bitrate_combo)
        audio_layout.addLayout(audio_bitrate_layout)
        
        self.audio_group.setLayout(audio_layout)
        layout.addWidget(self.audio_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_audio_tab(self):
        """
        Create and configure the audio settings tab
        
        Returns:
            QWidget: The audio settings tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        info_label = QLabel("Extract audio only from video")
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(info_label)
        
        # Audio format group box
        format_group = QGroupBox("Audio Format")
        format_layout = QVBoxLayout()
        self.audio_output_combo = QComboBox()
        self.audio_output_combo.addItems(["MP3", "AAC (M4A)", "FLAC"])
        format_layout.addWidget(self.audio_output_combo)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Audio quality group box
        quality_group = QGroupBox("Audio Quality")
        quality_layout = QVBoxLayout()
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems([
            "128 kbps", 
            "192 kbps", 
            "256 kbps", 
            "320 kbps"
        ])
        quality_layout.addWidget(self.audio_quality_combo)
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        # Audio settings group box
        settings_group = QGroupBox("Audio Settings")
        settings_layout = QVBoxLayout()
        
        settings_info = QLabel("Fixed settings: Stereo (2 channels), 48kHz sample rate")
        settings_info.setStyleSheet("color: #666666; font-size: 11px;")
        settings_layout.addWidget(settings_info)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    # --------------------------------------------------
    # Signal connections
    # --------------------------------------------------
    def setup_connections(self):
        """
        Connect UI signals to their corresponding slots
        """
        self.container_combo.currentTextChanged.connect(self.on_container_changed)
        self.quality_slider.valueChanged.connect(self.on_quality_slider_changed)
        self.video_audio_format_combo.currentTextChanged.connect(self.update_file_size_estimation)
        self.resolution_combo.currentTextChanged.connect(self.update_file_size_estimation)
        self.audio_output_combo.currentTextChanged.connect(self.on_audio_format_changed)
        self.container_combo.currentTextChanged.connect(self.update_ui_state)
        
    # --------------------------------------------------
    # Event handlers
    # --------------------------------------------------
    def on_container_changed(self):
        """
        Handle container format selection change
        Updates available codecs and enables/disables controls
        """
        container = self.container_combo.currentText()
        
        self.video_codec_combo.clear()
        
        if "Original" in container:
            # Original - Copy mode
            self.video_codec_combo.addItems(["Original"])
            self.video_codec_combo.setEnabled(False)
            self.video_codec_combo.setCurrentIndex(0)
            
            # Disable other controls in copy mode
            self.quality_slider.setEnabled(False)
            self.resolution_combo.setEnabled(False)
            self.video_audio_format_combo.setEnabled(False)
            self.video_audio_bitrate_combo.setEnabled(False)
            
            # Set values to Original
            self.resolution_combo.setCurrentText("Original")
            self.video_audio_format_combo.setCurrentText("Original")
            self.video_audio_bitrate_combo.setCurrentText("Original")
            
            self.file_size_label.setText("File size will match original (fast copy)")
            
        elif "MP4" in container:
            self.video_codec_combo.setEnabled(True)
            self.video_codec_combo.addItems(["H.264 (libx264)", "H.265 (libx265)"])
            self.video_codec_combo.setCurrentIndex(0)
            self.enable_all_controls()
        elif "Matroska" in container:
            self.video_codec_combo.setEnabled(True)
            self.video_codec_combo.addItems(["H.264 (libx264)", "H.265 (libx265)"])
            self.video_codec_combo.setCurrentIndex(0)
            self.enable_all_controls()
        elif "WebM" in container:
            self.video_codec_combo.setEnabled(True)
            self.video_codec_combo.addItems(["VP9 (libvpx-vp9)"])
            self.enable_all_controls()
        
        self.update_file_size_estimation()
        
    def enable_all_controls(self):
        """
        Enable all video-related controls
        Called when not in "Original - Copy" mode
        """
        self.quality_slider.setEnabled(True)
        self.resolution_combo.setEnabled(True)
        self.video_audio_format_combo.setEnabled(True)
        self.video_audio_bitrate_combo.setEnabled(True)
        
        if self.video_audio_format_combo.currentText() == "Original":
            self.video_audio_format_combo.setCurrentIndex(1)  # AAC
        if self.video_audio_bitrate_combo.currentText() == "Original":
            self.video_audio_bitrate_combo.setCurrentIndex(2)  # 192 kbps
        
    def update_ui_state(self):
        """
        Update UI appearance based on current settings
        Changes styles when in "Original - Copy" mode
        """
        container = self.container_combo.currentText()
        
        if "Original" in container:
            # Apply disabled styling for copy mode
            style = """
                QComboBox:disabled, QSlider:disabled {
                    color: #999999;
                    background-color: #f0f0f0;
                }
                QLabel {
                    color: #666666;
                }
            """
            self.quality_group.setStyleSheet("""
                QGroupBox {
                    color: #999999;
                }
            """)
            self.resolution_group.setStyleSheet("""
                QGroupBox {
                    color: #999999;
                }
            """)
            self.audio_group.setStyleSheet("""
                QGroupBox {
                    color: #999999;
                }
            """)
        else:
            # Clear styling for normal mode
            self.quality_group.setStyleSheet("")
            self.resolution_group.setStyleSheet("")
            self.audio_group.setStyleSheet("")
        
    def on_quality_slider_changed(self):
        """
        Handle quality slider value change
        Updates quality labels and CRF value
        """
        slider_value = self.quality_slider.value()
        crf_value = 29 - slider_value  # Calculate CRF value (inverse relationship)
        
        self.quality_value_label.setText(f"Quality: {slider_value}/10")
        self.crf_value_label.setText(f"CRF: {crf_value}")
        
        # Add quality description based on slider value
        quality_text = ""
        if slider_value >= 9:
            quality_text = "Excellent Quality"
        elif slider_value >= 7:
            quality_text = "High Quality"
        elif slider_value >= 5:
            quality_text = "Good Quality"
        elif slider_value >= 3:
            quality_text = "Medium Quality"
        else:
            quality_text = "Basic Quality"
            
        self.crf_value_label.setText(f"CRF: {crf_value} ({quality_text})")
        self.update_file_size_estimation()
        
    def update_file_size_estimation(self):
        """
        Estimate output file size based on current settings
        Updates the file size label with estimated MB per minute
        """
        try:
            slider_value = self.quality_slider.value()
            crf_value = 29 - slider_value
            
            base_size_per_minute = 0
            
            # Determine base size based on CRF value
            if crf_value <= 19:
                base_size_per_minute = 50
            elif crf_value <= 23:
                base_size_per_minute = 25
            elif crf_value <= 27:
                base_size_per_minute = 12
            elif crf_value <= 31:
                base_size_per_minute = 6
            else:
                base_size_per_minute = 3
                
            # Adjust for resolution
            resolution = self.resolution_combo.currentText()
            if "Original" in resolution:
                base_size_per_minute *= 1
            elif "4K" in resolution:
                base_size_per_minute *= 4
            elif "2K" in resolution:
                base_size_per_minute *= 2.25
            elif "1080p" in resolution:
                base_size_per_minute *= 1
            elif "720p" in resolution:
                base_size_per_minute *= 0.6
            elif "480p" in resolution:
                base_size_per_minute *= 0.3
                
            # Adjust for audio format
            audio_format = self.video_audio_format_combo.currentText()
            if "MP3" in audio_format:
                base_size_per_minute += 2
            elif "AAC" in audio_format:
                base_size_per_minute += 1.5
                
            self.file_size_label.setText(f"Estimated: ~{base_size_per_minute:.1f} MB per minute")
            
        except Exception as e:
            print(f"Error estimating file size: {e}")
            self.file_size_label.setText("Estimated file size: --")
        
    def on_audio_format_changed(self):
        """
        Handle audio format selection change in audio tab
        Updates available quality options
        """
        format_text = self.audio_output_combo.currentText()
        
        self.audio_quality_combo.clear()
        
        if "FLAC" in format_text:
            # FLAC is lossless, only one option
            self.audio_quality_combo.addItems(["Lossless"])
            self.audio_quality_combo.setEnabled(False)
        else:
            # MP3/AAC have multiple bitrate options
            self.audio_quality_combo.addItems([
                "128 kbps", 
                "192 kbps", 
                "256 kbps", 
                "320 kbps"
            ])
            self.audio_quality_combo.setEnabled(True)
            self.audio_quality_combo.setCurrentIndex(1)  # Default to 192 kbps
            
    # --------------------------------------------------
    # Settings management
    # --------------------------------------------------
    def load_current_settings(self):
        """
        Load existing settings into UI controls
        Called during initialization
        """
        # Determine which tab to show
        audio_output = self.settings.get("audio_output_format", "none")
        if audio_output != "none":
            self.tab_widget.setCurrentIndex(1)  # Audio tab
        else:
            self.tab_widget.setCurrentIndex(0)  # Video tab
        
        # Load container format
        format_index = self.settings.get("format_index", 0)
        if format_index == 0:
            self.container_combo.setCurrentText("Original - Copy")
        else:
            containers = ["Original - Copy", "MP4 (.mp4)", "Matroska (.mkv)", "WebM (.webm)"]
            if format_index < len(containers):
                self.container_combo.setCurrentText(containers[format_index])
            else:
                self.container_combo.setCurrentText("MP4 (.mp4)")
        
        self.on_container_changed()  # Update UI based on container
        
        # Load video codec
        video_codec = self.settings.get("video_codec", "Original")
        if video_codec in ["H.264 (libx264)", "H264"]:
            self.video_codec_combo.setCurrentText("H.264 (libx264)")
        elif video_codec in ["H.265 (libx265)", "H265"]:
            self.video_codec_combo.setCurrentText("H.265 (libx265)")
        elif video_codec in ["VP9 (libvpx-vp9)", "VP9"]:
            self.video_codec_combo.setCurrentText("VP9 (libvpx-vp9)")
        else:
            self.video_codec_combo.setCurrentText("Original")
        
        # Load quality settings
        crf_value = self.settings.get("crf_value", 23)
        slider_value = 29 - crf_value
        slider_value = max(1, min(10, slider_value))
        self.quality_slider.setValue(slider_value)
        self.on_quality_slider_changed()
        
        # Load resolution
        resolution = self.settings.get("resolution", "Original")
        resolutions = ["Original", "4K (3840x2160)", "2K (2560x1440)", 
                      "1080p (1920x1080)", "720p (1280x720)", "480p (854x480)"]
        
        if "Original" in resolution:
            self.resolution_combo.setCurrentIndex(0)
        else:
            for i, res in enumerate(resolutions):
                if resolution in res and i > 0:
                    self.resolution_combo.setCurrentIndex(i)
                    break
                
        # Load video audio format
        video_audio_format = self.settings.get("video_audio_format", "Original")
        if video_audio_format == "MP3":
            self.video_audio_format_combo.setCurrentText("MP3")
        elif video_audio_format == "AAC":
            self.video_audio_format_combo.setCurrentText("AAC")
        else:
            self.video_audio_format_combo.setCurrentText("Original")
            
        # Load video audio bitrate
        video_audio_bitrate = self.settings.get("video_audio_bitrate", "Original")
        for i in range(self.video_audio_bitrate_combo.count()):
            if video_audio_bitrate in self.video_audio_bitrate_combo.itemText(i):
                self.video_audio_bitrate_combo.setCurrentIndex(i)
                break
                
        # Load audio output format
        audio_output = self.settings.get("audio_output_format", "mp3")
        if audio_output == "mp3":
            self.audio_output_combo.setCurrentIndex(0)
        elif audio_output == "aac":
            self.audio_output_combo.setCurrentIndex(1)
        elif audio_output == "flac":
            self.audio_output_combo.setCurrentIndex(2)
            
        self.on_audio_format_changed()  # Update audio quality options
        
        # Load audio quality
        audio_quality = self.settings.get("audio_quality", "192 kbps")
        for i in range(self.audio_quality_combo.count()):
            if audio_quality in self.audio_quality_combo.itemText(i):
                self.audio_quality_combo.setCurrentIndex(i)
                break
                
        self.update_file_size_estimation()  # Update file size estimate
        self.update_ui_state()  # Update UI appearance
        
    def get_updated_settings(self):
        """
        Get current settings from UI controls
        
        Returns:
            dict: Dictionary containing all current settings
        """
        settings = {}
        
        if self.tab_widget.currentIndex() == 0:
            # Video export settings
            settings["audio_output_format"] = "none"
            
            container_text = self.container_combo.currentText()
            if "Original" in container_text:
                # Original copy mode
                settings["container"] = "Original - Copy"
                settings["format_index"] = 0
                settings["video_codec"] = "Original"
                settings["resolution"] = "Original"
                settings["video_audio_format"] = "Original"
                settings["video_audio_bitrate"] = "Original"
                settings["quality"] = "Original"
                settings["crf_value"] = 23
                settings["quality_slider"] = 6
            elif "MP4" in container_text:
                settings["container"] = "MP4 (.mp4)"
                settings["format_index"] = 1
            elif "Matroska" in container_text:
                settings["container"] = "Matroska (.mkv)"
                settings["format_index"] = 2
            elif "WebM" in container_text:
                settings["container"] = "WebM (.webm)"
                settings["format_index"] = 3
                
            if "Original" not in container_text:
                # Encode mode (not copy)
                codec_text = self.video_codec_combo.currentText()
                if "H.264" in codec_text:
                    settings["video_codec"] = "H264"
                elif "H.265" in codec_text:
                    settings["video_codec"] = "H265"
                elif "VP9" in codec_text:
                    settings["video_codec"] = "VP9"
                    
                # Quality settings
                slider_value = self.quality_slider.value()
                settings["crf_value"] = 29 - slider_value
                settings["quality_slider"] = slider_value
                
                # Resolution settings
                resolution_text = self.resolution_combo.currentText()
                if "Original" in resolution_text:
                    settings["resolution"] = "Original"
                    settings["quality"] = "Original"
                elif "4K" in resolution_text:
                    settings["resolution"] = "4K"
                    settings["quality"] = "4K"
                elif "2K" in resolution_text:
                    settings["resolution"] = "2K"
                    settings["quality"] = "2K"
                elif "1080p" in resolution_text:
                    settings["resolution"] = "1080p"
                    settings["quality"] = "1080p"
                elif "720p" in resolution_text:
                    settings["resolution"] = "720p"
                    settings["quality"] = "720p"
                elif "480p" in resolution_text:
                    settings["resolution"] = "480p"
                    settings["quality"] = "480p"
                else:
                    settings["resolution"] = "Original"
                    settings["quality"] = "Original"
                    
                # Audio settings for video
                audio_format_text = self.video_audio_format_combo.currentText()
                if "MP3" in audio_format_text:
                    settings["video_audio_format"] = "MP3"
                elif "AAC" in audio_format_text:
                    settings["video_audio_format"] = "AAC"
                else:
                    settings["video_audio_format"] = "Original"
                    
                # Audio bitrate for video
                audio_bitrate_text = self.video_audio_bitrate_combo.currentText()
                if "Original" in audio_bitrate_text:
                    settings["video_audio_bitrate"] = "Original"
                    settings["video_audio_quality"] = "Original"
                else:
                    settings["video_audio_bitrate"] = audio_bitrate_text.split(" ")[0]
                    settings["video_audio_quality"] = audio_bitrate_text.split(" ")[0]
                
        else:
            # Audio only export settings
            audio_format_text = self.audio_output_combo.currentText()
            if "MP3" in audio_format_text:
                settings["audio_output_format"] = "mp3"
            elif "AAC" in audio_format_text:
                settings["audio_output_format"] = "aac"
            elif "FLAC" in audio_format_text:
                settings["audio_output_format"] = "flac"
                
            # Set video-related settings to defaults for audio export
            settings["format_index"] = 0
            settings["video_codec"] = "Original"
            settings["quality"] = "Original"
            settings["resolution"] = "Original"
            settings["video_audio_format"] = "Original"
            settings["video_audio_quality"] = "Original"
            
            # Audio quality for audio export
            audio_quality_text = self.audio_quality_combo.currentText()
            if "Lossless" in audio_quality_text:
                settings["audio_quality"] = "Lossless"
            else:
                settings["audio_quality"] = audio_quality_text.split(" ")[0]
                
        return settings