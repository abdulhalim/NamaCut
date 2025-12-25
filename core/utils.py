import os
import subprocess
import re
import json

# --------------------------------------------------
# Time conversion
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
# File detection
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
# Video information
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
# File management
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
# FFmpeg progress parsing
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
# Formatting utilities
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