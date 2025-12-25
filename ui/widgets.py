# --------------------------------------------------
# Widgets Module
# Contains custom UI widgets for the video editor application
# --------------------------------------------------

import os
import subprocess
import re
from datetime import timedelta
from PyQt5.QtWidgets import QPushButton, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import qtawesome as qta

# --------------------------------------------------
# IconButton Class
# Custom button with Font Awesome icon support
# --------------------------------------------------
class IconButton(QPushButton):
    def __init__(self, icon_name, text='', parent=None):
        super().__init__(parent)
        try:
            icon = qta.icon(icon_name)
            self.setIcon(icon)
        except Exception:
            pass
        self.setText(text)
        
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                border: 1px solid #3f8e93;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #bbdefb;
            }
            QPushButton:disabled {
                background-color: #eeeeee;
                color: #999999;
                border-color: #cccccc;
            }
        """)

# --------------------------------------------------
# VideoPlayer Class
# Main video player widget with drag and drop support
# --------------------------------------------------
class VideoPlayer(QWidget):
    fileDropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.placeholder = QLabel("Drop video file here or use 'Select Video File'")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                padding: 40px;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
        """)
        self.layout.addWidget(self.placeholder)
        
        self.video_widget = None
        
    # --------------------------------------------------
    # Drag and Drop Event Handlers
    # --------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
                if os.path.splitext(file_path)[1].lower() in video_extensions:
                    event.acceptProposedAction()
                    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.fileDropped.emit(file_path)
                event.acceptProposedAction()
    
    # --------------------------------------------------
    # Video Loading and Management
    # --------------------------------------------------
    def load_video(self, file_path):
        from ui.media_player import MediaPlayer
        
        if self.placeholder:
            self.layout.removeWidget(self.placeholder)
            self.placeholder.hide()
            self.placeholder.deleteLater()
            self.placeholder = None
        
        if not self.video_widget:
            self.video_widget = MediaPlayer(self)
            self.layout.addWidget(self.video_widget)
        
        return self.video_widget.load_video(file_path)
    
    def get_video_widget(self):
        return self.video_widget
    
    # --------------------------------------------------
    # Playback Control Methods
    # --------------------------------------------------
    def play(self):
        if self.video_widget:
            self.video_widget.play()
    
    def pause(self):
        if self.video_widget:
            self.video_widget.pause()
    
    def stop(self):
        """Force stop the video player"""
        if self.video_widget:
            try:
                self.video_widget.stop()
                
                if hasattr(self.video_widget, 'media_player'):
                    self.video_widget.media_player.pause()
                    self.video_widget.media_player.stop()
                    self.video_widget.media_player.setVolume(0)
                    self.video_widget.media_player.setMedia(None)
                    
                print("VideoPlayer: Force stop completed")
                
            except Exception as e:
                print(f"VideoPlayer stop error: {e}")
    
    def set_position(self, position_ms):
        if self.video_widget:
            self.video_widget.set_position_ms(position_ms)
    
    def get_current_time(self):
        if self.video_widget:
            return self.video_widget.get_current_time()
        return 0
    
    # --------------------------------------------------
    # Video Transformation Methods
    # --------------------------------------------------
    def rotate_left(self):
        if self.video_widget:
            self.video_widget.rotate_left()
    
    def rotate_right(self):
        if self.video_widget:
            self.video_widget.rotate_right()
    
    def flip_horizontal(self):
        if self.video_widget:
            self.video_widget.flip_h()
    
    def flip_vertical(self):
        if self.video_widget:
            self.video_widget.flip_v()
    
    def reset_transformations(self):
        if self.video_widget:
            self.video_widget.reset_transformations()
    
    def toggle_crop_mode(self):
        if self.video_widget:
            return self.video_widget.toggle_crop_mode()
        return False

# --------------------------------------------------
# Time Conversion Utilities
# Convert between different time representations
# --------------------------------------------------
def seconds_to_hmsms(total_seconds):
    if total_seconds is None:
        return 0, 0, 0, 0
        
    total_seconds = float(total_seconds)
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return hours, minutes, seconds, milliseconds

def hmsms_str(total_seconds):
    if total_seconds is None:
        return "00:00:00.000"
        
    h, m, s, ms = seconds_to_hmsms(total_seconds)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def hmsms_to_seconds(hours, minutes, seconds, milliseconds):
    try:
        total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + int(seconds) + (float(milliseconds) / 1000)
        return total_seconds
    except (ValueError, TypeError):
        return 0.0

def milliseconds_to_hmsms(milliseconds):
    if milliseconds is None:
        return 0, 0, 0, 0
        
    total_seconds = milliseconds / 1000
    return seconds_to_hmsms(total_seconds)

def hmsms_str_from_ms(milliseconds):
    if milliseconds is None:
        return "00:00:00.000"
        
    h, m, s, ms = milliseconds_to_hmsms(milliseconds)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

# --------------------------------------------------
# File Detection Utilities
# Determine if a file is a valid video file
# --------------------------------------------------
def get_file_type(file_path):
    if not file_path or not os.path.exists(file_path):
        return None
        
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0",
            file_path
        ], capture_output=True, text=True, check=True, timeout=10)
        
        return "video" if result.stdout.strip() == "video" else None
    except subprocess.TimeoutExpired:
        print(f"Timeout detecting file type: {file_path}")
        return None
    except Exception as e:
        print(f"Error detecting file type {file_path}: {e}")
        return None

def is_video_file(file_path):
    if not file_path or not os.path.exists(file_path):
        return False
        
    video_extensions = {
        '.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.flv', 
        '.m4v', '.3gp', '.mpg', '.mpeg', '.m4v', '.ts', '.mts', '.m2ts',
        '.ogv', '.qt', '.rm', '.rmvb', '.asf', '.vob'
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in video_extensions:
        return False
        
    file_type = get_file_type(file_path)
    return file_type == "video"

# --------------------------------------------------
# Video Information Utilities
# Extract metadata from video files using ffprobe
# --------------------------------------------------
def get_video_duration(file_path):
    if not file_path or not os.path.exists(file_path):
        return 0
        
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ], capture_output=True, text=True, check=True, timeout=10)
        
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting video duration {file_path}: {e}")
        return 0

def get_video_info(file_path):
    if not file_path or not os.path.exists(file_path):
        return {}
        
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,r_frame_rate",
            "-show_entries", "format=duration,size",
            "-of", "json", file_path
        ], capture_output=True, text=True, check=True, timeout=10)
        
        import json
        info = json.loads(result.stdout)
        
        video_info = {}
        if 'streams' in info and info['streams']:
            stream = info['streams'][0]
            video_info.update({
                'codec': stream.get('codec_name', 'unknown'),
                'width': stream.get('width', 0),
                'height': stream.get('height', 0),
                'frame_rate': stream.get('r_frame_rate', '0/0')
            })
            
        if 'format' in info:
            format_info = info['format']
            video_info.update({
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0))
            })
            
        return video_info
        
    except Exception as e:
        print(f"Error getting video info {file_path}: {e}")
        return {}

# --------------------------------------------------
# File Management Utilities
# Handle output directories and file paths
# --------------------------------------------------
def get_output_directory(format_type):
    home_dir = os.path.expanduser("~")
    
    audio_formats = {"mp3", "aac", "wav", "flac", "m4a", "ogg"}
    video_formats = {"mp4", "mkv", "webm", "avi", "mov", "wmv", "flv", "mpeg", "ts"}
    
    if format_type.lower() in audio_formats:
        output_dir = os.path.join(home_dir, "Music", "NamaCut_Output")
    elif format_type.lower() in video_formats or format_type == "original":
        output_dir = os.path.join(home_dir, "Videos", "NamaCut_Output")
    else:
        output_dir = os.path.join(home_dir, "NamaCut_Output")
    
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def unique_output_path(base_name, extension, format_type):
    output_dir = get_output_directory(format_type)
    base_path = os.path.join(output_dir, base_name)
    candidate = f"{base_path}{extension}"
    
    if not os.path.exists(candidate):
        return candidate
    
    i = 1
    while True:
        candidate = f"{base_path}({i}){extension}"
        if not os.path.exists(candidate):
            return candidate
        i += 1

def cleanup_incomplete_files(output_file):
    try:
        if output_file and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            if file_size < 1024 * 1024:
                os.remove(output_file)
                print(f"Removed incomplete file: {output_file}")
                return True
    except Exception as e:
        print(f"Error cleaning up incomplete file: {e}")
    
    return False

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

# --------------------------------------------------
# FFmpeg Progress Parsing
# Parse progress information from FFmpeg output
# --------------------------------------------------
def parse_ffmpeg_progress(line, total_duration):
    if not line or total_duration <= 0:
        return None
        
    patterns = [
        r'time=(\d+):(\d+):(\d+\.\d+)',
        r'time=(\d+):(\d+):(\d+)',
        r'time=(\d+\.\d+)',
        r'time=(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            try:
                if len(match.groups()) == 3:
                    hours, minutes, seconds = map(float, match.groups())
                    current_time = hours * 3600 + minutes * 60 + seconds
                else:
                    current_time = float(match.group(1))
                
                progress = min(current_time / total_duration, 1.0)
                return progress
            except (ValueError, TypeError):
                continue
                
    return None

# --------------------------------------------------
# Formatting Utilities
# Format file sizes for display
# --------------------------------------------------
def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f} {size_names[i]}"