# utils.py
import os
import subprocess
import re

# Time Conversion Utilities
def seconds_to_hmsms(s):
    s = float(s)
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = int(s % 60)
    milliseconds = int((s - int(s)) * 1000)
    return hours, minutes, seconds, milliseconds

def hmsms_str(s):
    h, m, sec, ms = seconds_to_hmsms(s)
    return f"{h:02d}:{m:02d}:{sec:02d}.{ms:03d}"

def hmsms_to_seconds(h, m, s, ms):
    return int(h)*3600 + int(m)*60 + int(s) + float(ms)/1000

# File Type Detection
def get_file_type(file_path):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0",
            file_path
        ], capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            return "video"
        else:
            return None
    except Exception as e:
        print(f"Error detecting file type: {e}")
        return None

def is_video_file(file_path):
    video_extensions = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.flv', '.m4v', 
                       '.3gp', '.mpg', '.mpeg', '.m4v', '.ts', '.mts', '.m2ts'}
    ext = os.path.splitext(file_path)[1].lower()
    if ext in video_extensions:
        file_type = get_file_type(file_path)
        return file_type == "video"
    return False

# Output Path Management
def get_output_directory(format_type):
    home_dir = os.path.expanduser("~")
    
    audio_formats = {"mp3", "aac", "wav", "flac", "m4a"}
    
    if format_type.lower() in audio_formats:
        output_dir = os.path.join(home_dir, "Music", "NamaCut_Output")
    else:
        output_dir = os.path.join(home_dir, "Videos", "NamaCut_Output")
    
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

# File Cleanup
def cleanup_incomplete_files(output_file):
    try:
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            if file_size < 1024 * 1024:
                os.remove(output_file)
                print(f"Removed incomplete file: {output_file}")
    except Exception as e:
        print(f"Error cleaning up incomplete file: {e}")

# FFmpeg Progress Parsing
def parse_ffmpeg_progress(line, total_duration):
    if not line:
        return None
    patterns = [
        r'time=(\d+):(\d+):(\d+\.\d+)',
        r'time=(\d+):(\d+):(\d+)',
        r'time=(\d+\.\d+)',
        r'time=(\d+)'
    ]
    for pattern in patterns:
        m = re.search(pattern, line)
        if m:
            if len(m.groups()) == 3:
                h, mm, ss = map(float, m.groups())
                current_time = h * 3600 + mm * 60 + ss
            else:
                current_time = float(m.group(1))
            if total_duration > 0:
                return min(current_time / total_duration, 1.0)
    return None
