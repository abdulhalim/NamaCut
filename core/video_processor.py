# --------------------------------------------------
# Video processing and export management
# --------------------------------------------------
import os
import subprocess
import json
from PyQt5.QtCore import QObject, pyqtSignal, QProcess
from .utils import parse_ffmpeg_progress


class VideoProcessor(QObject):
    progress_updated = pyqtSignal(int)
    export_finished = pyqtSignal(str, bool)
    export_started = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_process = None
        self.is_processing = False
        self.abort_requested = False
        self.output_file = None
        self.temp_output_file = None
        self.total_duration = 0
        
    def _get_temp_filename(self, output_path):
        """Generate temporary filename with proper extension"""
        base, ext = os.path.splitext(output_path)
        return f"{base}.tmp{ext}"
        
    def export_video(self, input_path, output_path, settings, start_time, end_time, video_filters=None):
        """Main video export function with VC-1 detection"""
        if not os.path.exists(input_path):
            self.export_finished.emit(output_path, False)
            return False
            
        self.output_file = output_path
        self.temp_output_file = self._get_temp_filename(output_path)
        
        duration = end_time - start_time
        self.total_duration = duration
        
        format_index = settings.get("format_index", 0)
        
        # Debug information
        print(f"\n=== EXPORT DEBUG ===")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        print(f"Temp: {self.temp_output_file}")
        print(f"Start: {start_time}, End: {end_time}, Duration: {duration}")
        print(f"Format index: {format_index}")
        print(f"Video filters: {video_filters}")
        
        # Check if video uses VC-1 codec
        is_vc1 = self.is_vc1_video(input_path)
        if is_vc1:
            print(f"Detected VC-1/WMV video codec")
        print(f"===================\n")
        
        # Select appropriate command based on format and codec
        if format_index == 0 and not video_filters:
            cmd = self.build_fast_copy_command(input_path, self.temp_output_file, start_time, duration, video_filters)
        else:
            if is_vc1:
                # Use special conversion command for VC-1
                cmd = self.build_vc1_conversion_command(input_path, self.temp_output_file, settings, start_time, duration, video_filters)
            else:
                cmd = self.build_video_command(input_path, self.temp_output_file, settings, start_time, duration, video_filters)
        
        if not cmd:
            return False
            
        self.export_started.emit()
        return self._run_ffmpeg_process(cmd)
        
    def export_audio(self, input_path, output_path, settings, start_time, end_time):
        """Export audio only from video file"""
        if not os.path.exists(input_path):
            self.export_finished.emit(output_path, False)
            return False
            
        self.output_file = output_path
        self.temp_output_file = self._get_temp_filename(output_path)
        
        duration = end_time - start_time
        self.total_duration = duration
        
        cmd = self.build_audio_command(input_path, self.temp_output_file, settings, start_time, duration)
        if not cmd:
            return False
            
        self.export_started.emit()
        return self._run_ffmpeg_process(cmd)
        
    def build_fast_copy_command(self, input_path, output_path, start_time, duration, video_filters=None):
        """Build FFmpeg command for fast copy (no re-encoding)"""
        cmd = ["ffmpeg", "-y"]
        
        cmd.extend(["-ss", str(start_time), "-i", input_path, "-t", str(duration)])
        
        if video_filters:
            cmd.extend(["-vf", video_filters])
            cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-c:v", "copy", "-c:a", "copy"])
        
        if output_path.endswith('.mp4'):
            cmd.extend(["-movflags", "+faststart"])
        
        cmd.append(output_path)
        
        return cmd
        
    def build_video_command(self, input_path, output_path, settings, start_time, duration, video_filters):
        """Build FFmpeg command for video conversion with re-encoding"""
        cmd = ["ffmpeg", "-y"]
        
        cmd.extend(["-ss", str(start_time), "-i", input_path, "-t", str(duration)])
        
        format_index = settings.get("format_index", 0)
        
        if format_index == 0:
            cmd.extend(["-c:v", "copy", "-c:a", "copy"])
            
            if video_filters:
                cmd.extend(["-vf", video_filters])
                cmd.remove("-c:v")
                cmd.remove("copy")
                cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-crf", "18"])
        else:
            # Build filter chain
            filter_chain = []
            
            # Add transformation filters (crop, rotate, flip)
            if video_filters:
                filter_chain.append(video_filters)
            
            # Add scale filter for resolution change
            resolution_params = self._get_resolution_params(settings, input_path)
            if resolution_params:
                # Extract just the filter part (remove "-vf" prefix)
                scale_filter = resolution_params[1] if len(resolution_params) > 1 else ""
                if scale_filter:
                    filter_chain.append(scale_filter)
            
            # Combine all filters
            if filter_chain:
                combined_filters = ",".join(filter_chain)
                cmd.extend(["-vf", combined_filters])
            
            # Add codec parameters
            codec_params = self._get_video_codec_params(settings, format_index)
            if codec_params:
                cmd.extend(codec_params)
            
            # Add audio parameters
            audio_params = self._get_audio_params(settings, format_index)
            if audio_params:
                cmd.extend(audio_params)
            
            # Add standard audio settings
            audio_settings = self._get_audio_settings(settings)
            if audio_settings:
                cmd.extend(audio_settings)
        
        if output_path.endswith('.mp4'):
            cmd.extend(["-movflags", "+faststart"])
        
        cmd.append(output_path)
        
        # Debug output
        print(f"\n=== FFMPEG COMMAND ===")
        print(f"Video filters: {video_filters}")
        print(f"Resolution params: {resolution_params if 'resolution_params' in locals() else 'None'}")
        print(f"Full command: {' '.join(cmd)}")
        print(f"===================================\n")
        
        return cmd
        
    def build_audio_command(self, input_path, output_path, settings, start_time, duration):
        """Build FFmpeg command for audio-only export"""
        cmd = [
            "ffmpeg", "-y", 
            "-ss", str(start_time), 
            "-i", input_path, 
            "-t", str(duration), 
            "-vn",
            "-ac", "2",
            "-ar", "48000"
        ]
        
        audio_format = settings.get("audio_output_format", "mp3")
        audio_quality = settings.get("audio_quality", "192")
        
        if audio_format == "mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", f"{audio_quality}k"])
        elif audio_format == "aac":
            cmd.extend(["-c:a", "aac", "-b:a", f"{audio_quality}k"])
        elif audio_format == "flac":
            cmd.extend(["-c:a", "flac"])
            
        cmd.append(output_path)
        return cmd
        
    def _get_video_codec_params(self, settings, format_index):
        """Get video codec parameters based on settings"""
        formats = ["original", "mp4", "mkv", "webm"]
        
        if format_index >= len(formats):
            format_index = 1
            
        format_type = formats[format_index]
        
        if format_type == "original":
            video_codec = self.detect_video_codec_from_file(settings.get("input_path", ""))
            if video_codec:
                return ["-c:v", video_codec, "-c:a", "copy"]
            else:
                return ["-c:v", "copy", "-c:a", "copy"]
        elif format_type == "webm":
            crf_value = settings.get("crf_value", 23)
            return ["-c:v", "libvpx-vp9", "-crf", str(crf_value), "-b:v", "0"]
        else:
            video_codec = settings.get("video_codec", "H264")
            crf_value = settings.get("crf_value", 23)
            
            if video_codec == "H265":
                return ["-c:v", "libx265", "-crf", str(crf_value), "-preset", "medium"]
            else:
                return ["-c:v", "libx264", "-crf", str(crf_value), "-preset", "medium"]
        
    def _get_audio_params(self, settings, format_index):
        """Get audio codec parameters based on settings"""
        formats = ["original", "mp4", "mkv", "webm"]
        format_type = formats[format_index] if format_index < len(formats) else "mp4"
        
        video_audio_format = settings.get("video_audio_format", "AAC")
        
        if format_type == "original":
            return ["-c:a", "copy"]
        elif format_type == "webm":
            return ["-c:a", "libopus", "-b:a", "192k"]
        elif video_audio_format == "Copy Original":
            return ["-c:a", "copy"]
        elif video_audio_format == "MP3":
            audio_bitrate = settings.get("video_audio_bitrate", "192")
            return ["-c:a", "libmp3lame", "-b:a", f"{audio_bitrate}k"]
        else:
            audio_bitrate = settings.get("video_audio_bitrate", "192")
            return ["-c:a", "aac", "-b:a", f"{audio_bitrate}k"]
        
    def _get_resolution_params(self, settings, input_path):
        """Get resolution scaling parameters"""
        resolution = settings.get("resolution", "Original")
        
        if resolution == "Original":
            return []
        
        # Get original video dimensions
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "json", input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            data = json.loads(result.stdout)
            
            if "streams" in data and len(data["streams"]) > 0:
                orig_width = int(data["streams"][0].get("width", 0))
                orig_height = int(data["streams"][0].get("height", 0))
                
                if orig_width == 0 or orig_height == 0:
                    return []
        except Exception as e:
            print(f"Error getting video dimensions: {e}")
            return []
        
        # Calculate target dimensions while preserving aspect ratio
        if resolution == "4K":
            target_width, target_height = 3840, 2160
        elif resolution == "2K":
            target_width, target_height = 2560, 1440
        elif resolution == "1080p":
            target_width, target_height = 1920, 1080
        elif resolution == "720p":
            target_width, target_height = 1280, 720
        elif resolution == "480p":
            target_width, target_height = 854, 480
        else:
            return []
        
        # Ensure dimensions are even numbers (required by most codecs)
        target_width = target_width if target_width % 2 == 0 else target_width - 1
        target_height = target_height if target_height % 2 == 0 else target_height - 1
        
        # Calculate new dimensions that fit within target while preserving aspect ratio
        orig_ratio = orig_width / orig_height
        target_ratio = target_width / target_height
        
        if abs(orig_ratio - target_ratio) < 0.01:
            # Same aspect ratio, direct scale
            new_width = target_width
            new_height = target_height
        else:
            # Different aspect ratio - fit within target dimensions
            if orig_ratio > target_ratio:
                # Video is wider than target, fit by width
                new_width = target_width
                new_height = int(target_width / orig_ratio)
            else:
                # Video is taller than target, fit by height
                new_height = target_height
                new_width = int(target_height * orig_ratio)
        
        # Ensure dimensions are even numbers
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        # Ensure minimum dimensions
        if new_width < 2 or new_height < 2:
            return []
        
        return ["-vf", f"scale={new_width}:{new_height}"]
        
    def _get_audio_settings(self, settings):
        """Get standard audio settings"""
        return ["-ac", "2", "-ar", "48000"]
        
    def detect_video_codec_from_file(self, input_path):
        """Detect video codec from file using ffprobe"""
        if not input_path or not os.path.exists(input_path):
            return None
        
        try:
            cmd = [
                "ffprobe", "-v", "error", 
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "json", input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
            data = json.loads(result.stdout)
            
            if "streams" in data and len(data["streams"]) > 0:
                codec_name = data["streams"][0].get("codec_name", "")
                # Map codec names to FFmpeg encoder names
                codec_map = {
                    "h264": "libx264",
                    "hevc": "libx265",
                    "h265": "libx265",
                    "vp8": "libvpx",
                    "vp9": "libvpx-vp9",
                    "av1": "libaom-av1",
                    "mpeg4": "mpeg4",
                    "msmpeg4v3": "msmpeg4v3",
                    "wmv3": "libx264",
                    "vc1": "libx264",
                    "wmva": "libx264",
                    "wmvp": "libx264",
                    "wmv1": "libx264",
                    "wmv2": "libx264",
                    "mpeg2video": "mpeg2video",
                    "mjpeg": "mjpeg"
                }
                return codec_map.get(codec_name, codec_name)
                
        except Exception as e:
            print(f"Error detecting codec: {e}")
        
        return None
        
    def _run_ffmpeg_process(self, cmd):
        """Run FFmpeg process and handle signals"""
        self.is_processing = True
        self.abort_requested = False
        
        try:
            print(f"Starting FFmpeg process...")
            self.current_process = QProcess()
            self.current_process.readyReadStandardError.connect(self._handle_stderr)
            self.current_process.finished.connect(self._process_finished)
            
            self.current_process.start(cmd[0], cmd[1:])
            return True
            
        except Exception as e:
            print(f"Error starting FFmpeg: {e}")
            self.is_processing = False
            return False
        
    def _handle_stderr(self):
        """Handle FFmpeg stderr output and parse progress"""
        if self.current_process:
            data = self.current_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            lines = data.split('\n')
            for line in lines:
                if line.strip():
                    print(f"FFmpeg: {line}")
                    progress = parse_ffmpeg_progress(line, self.total_duration)
                    if progress is not None:
                        self.progress_updated.emit(int(progress * 100))
    
    def _process_finished(self, exit_code, exit_status):
        """Handle FFmpeg process completion"""
        success = (exit_code == 0) and (not self.abort_requested)
        self.is_processing = False
        
        if success and hasattr(self, 'temp_output_file') and self.temp_output_file:
            try:
                if os.path.exists(self.temp_output_file):
                    with open(self.temp_output_file, 'rb+') as f:
                        os.fsync(f.fileno())
            except Exception as e:
                print(f"Error syncing temp file: {e}")
            
            try:
                if os.path.exists(self.temp_output_file):
                    os.rename(self.temp_output_file, self.output_file)
                    print(f"Successfully renamed temp file to: {self.output_file}")
                    
                    try:
                        with open(self.output_file, 'rb+') as f:
                            os.fsync(f.fileno())
                    except Exception as e:
                        print(f"Error syncing final file: {e}")
                else:
                    print(f"Warning: Temp file does not exist: {self.temp_output_file}")
                    success = False
            except Exception as e:
                print(f"Error renaming temp file: {e}")
                success = False
        elif not success:
            self._cleanup_temp_file()
            self._cleanup_incomplete_file(self.output_file)
        else:
            print("Warning: No temp file to rename")
        
        if success:
            self.export_finished.emit(self.output_file, True)
        else:
            if self.abort_requested:
                self._cleanup_temp_file()
                self._cleanup_file(self.output_file)
                self.export_finished.emit(self.output_file, False)
            else:
                self._cleanup_temp_file()
                self._cleanup_incomplete_file(self.output_file)
                self.export_finished.emit(self.output_file, False)
        
        self.current_process = None
    
    def _cleanup_temp_file(self):
        """Clean up temporary file"""
        try:
            if hasattr(self, 'temp_output_file') and self.temp_output_file:
                if os.path.exists(self.temp_output_file):
                    os.remove(self.temp_output_file)
                    print(f"Removed temp file: {self.temp_output_file}")
        except Exception as e:
            print(f"Error cleaning up temp file: {e}")

    def _cleanup_incomplete_file(self, output_file):
        """Clean up incomplete output files (< 1MB)"""
        try:
            if output_file and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                if file_size < 1024 * 1024:
                    os.remove(output_file)
                    print(f"Removed incomplete/corrupt file (under 1MB): {output_file}")
        except Exception as e:
            print(f"Error cleaning up file: {e}")

    def _cleanup_file(self, output_file):
        """Clean up output file"""
        try:
            if output_file and os.path.exists(output_file):
                os.remove(output_file)
                print(f"Removed incomplete file: {output_file}")
        except Exception as e:
            print(f"Error cleaning up file: {e}")

    def abort_processing(self):
        """Abort current FFmpeg process"""
        self.abort_requested = True
        if self.current_process and self.current_process.state() == QProcess.Running:
            print("Terminating FFmpeg process...")
            
            self.current_process.terminate()
            
            if not self.current_process.waitForFinished(3000):
                print("FFmpeg not responding to terminate, trying kill...")
                self.current_process.kill()
                
                if not self.current_process.waitForFinished(2000):
                    print("Forcing FFmpeg process cleanup...")
                    self.current_process = None
                    self.is_processing = False
            else:
                self.is_processing = False
                print("FFmpeg process terminated successfully")
    
    def wait_for_completion(self, timeout_ms=5000):
        """Wait for FFmpeg process to complete"""
        if self.current_process and self.current_process.state() == QProcess.Running:
            print(f"Waiting for FFmpeg to complete (timeout: {timeout_ms}ms)...")
            return self.current_process.waitForFinished(timeout_ms)
        return True

    def is_vc1_video(self, input_path):
        """Check if video uses VC-1 codec family"""
        try:
            cmd = [
                "ffprobe", "-v", "error", 
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "json", input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            data = json.loads(result.stdout)
            
            if "streams" in data and len(data["streams"]) > 0:
                codec_name = data["streams"][0].get("codec_name", "").lower()
                return codec_name in ["wmv3", "vc1", "wmva", "wmvp", "wmv1", "wmv2"]
        except Exception as e:
            print(f"Error checking VC-1: {e}")
        return False

    def build_vc1_conversion_command(self, input_path, output_path, settings, start_time, duration, video_filters):
        """Build special FFmpeg command for converting VC-1/WMV videos"""
        cmd = ["ffmpeg", "-y"]
        
        # For VC-1, use -ss after -i for better accuracy
        cmd.extend(["-i", input_path])
        cmd.extend(["-ss", str(start_time), "-t", str(duration)])
        
        # Get target codec from settings
        video_codec = settings.get("video_codec", "H264")
        crf_value = settings.get("crf_value", 23)
        
        # Set video codec and parameters
        if video_codec == "H265":
            cmd.extend(["-c:v", "libx265"])
            cmd.extend(["-crf", str(crf_value)])
            cmd.extend(["-preset", "medium"])
            cmd.extend(["-tag:v", "hvc1"])  # For better compatibility
        elif video_codec == "VP9":
            cmd.extend(["-c:v", "libvpx-vp9"])
            cmd.extend(["-crf", str(crf_value)])
            cmd.extend(["-b:v", "0"])  # Variable bitrate for VP9
        else:  # Default to H.264
            cmd.extend(["-c:v", "libx264"])
            cmd.extend(["-crf", str(crf_value)])
            cmd.extend(["-preset", "medium"])
        
        # Audio settings
        audio_format = settings.get("video_audio_format", "AAC")
        audio_bitrate = settings.get("video_audio_bitrate", "192")
        
        if audio_format == "MP3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", f"{audio_bitrate}k"])
        else:
            cmd.extend(["-c:a", "aac", "-b:a", f"{audio_bitrate}k"])
        
        # Build filter chain
        filter_chain = []
        
        # Add transformation filters
        if video_filters:
            filter_chain.append(video_filters)
        
        # Add scale filter for resolution change
        resolution = settings.get("resolution", "Original")
        if resolution != "Original":
            res_params = self._get_resolution_params(settings, input_path)
            if res_params:
                scale_filter = res_params[1] if len(res_params) > 1 else ""
                if scale_filter:
                    filter_chain.append(scale_filter)
        
        # Combine all filters
        if filter_chain:
            combined_filters = ",".join(filter_chain)
            cmd.extend(["-vf", combined_filters])
        
        # Add faststart for MP4 files
        if output_path.endswith('.mp4'):
            cmd.extend(["-movflags", "+faststart"])
        
        # Compatibility flags
        cmd.extend(["-strict", "-2"])  # Allow experimental codecs
        cmd.extend(["-pix_fmt", "yuv420p"])  # Ensure compatibility
        
        cmd.append(output_path)
        
        # Debug output
        print(f"\n=== VC-1 CONVERSION COMMAND ===")
        print(f"Target codec: {video_codec}")
        print(f"Video filters: {video_filters}")
        print(f"Full command: {' '.join(cmd)}")
        print(f"===================================\n")
        
        return cmd
