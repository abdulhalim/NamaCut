# export.py
import gi
import os
import subprocess
import threading
import time

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gtk, GLib

from modules.utils import *

# Export Manager Class
class ExportManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_process = None
        self.is_processing = False
        self.current_output_file = None
        self.abort_requested = False
    
    def start_export(self):
        if self.is_processing:
            return
        
        if not self.main_window.player.uri:
            self.main_window.show_error_dialog("No File Selected", "Please select a video file first.")
            return
        
        if self.main_window.player.is_playing:
            self.main_window.player.pause()
        
        valid, msg = self.main_window.validate_times()
        if not valid:
            self.main_window.show_error_dialog("Invalid Time Range", msg)
            return
        
        self.abort_requested = False
        audio_output_format = self.main_window.settings.get("audio_output_format", "mp3")
        
        if audio_output_format != "none":
            self.export_audio(audio_output_format)
        else:
            self.export_video()
    
    # Audio Export Logic
    def export_audio(self, audio_format):
        input_path = self.main_window.player.uri
        input_name = os.path.splitext(os.path.basename(input_path))[0]
        
        if audio_format == "flac":
            flac_level = self.main_window.settings.get("flac_compression_level", "5")
            quality_suffix = f"L{flac_level}"
            ext = ".flac"
        elif audio_format == "wav":
            quality_suffix = "lossless"
            ext = ".wav"
        elif audio_format == "aac":
            audio_quality = self.main_window.settings.get("audio_quality", "192")
            quality_suffix = audio_quality
            ext = ".m4a"
        else:
            audio_quality = self.main_window.settings.get("audio_quality", "192")
            quality_suffix = audio_quality
            ext = ".mp3"
        
        base_name = f"{input_name}.{quality_suffix}"
        output_file = unique_output_path(base_name, ext, audio_format)
        
        start = hmsms_to_seconds(
            self.main_window.start_h.get_value_as_int(), 
            self.main_window.start_m.get_value_as_int(), 
            self.main_window.start_s.get_value_as_int(),
            self.main_window.start_ms.get_value_as_int()
        )
        end = hmsms_to_seconds(
            self.main_window.end_h.get_value_as_int(), 
            self.main_window.end_m.get_value_as_int(), 
            self.main_window.end_s.get_value_as_int(),
            self.main_window.end_ms.get_value_as_int()
        )
        duration = end - start
        
        cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-i", input_path, 
            "-t", str(duration), "-vn"
        ]
        
        if audio_format == "mp3":
            audio_quality = self.main_window.settings.get("audio_quality", "192")
            cmd.extend(["-c:a", "libmp3lame", "-b:a", f"{audio_quality}k"])
        elif audio_format == "aac":
            audio_quality = self.main_window.settings.get("audio_quality", "192")
            cmd.extend(["-c:a", "aac", "-b:a", f"{audio_quality}k"])
        elif audio_format == "wav":
            cmd.extend(["-c:a", "pcm_s16le"])
        elif audio_format == "flac":
            flac_level = self.main_window.settings.get("flac_compression_level", "5")
            cmd.extend(["-c:a", "flac", "-compression_level", flac_level])
        
        cmd.append(output_file)
        
        self._start_export_process(cmd, duration, output_file)
    
    # Video Export Logic
    def export_video(self):
        format_type = self.main_window.get_selected_format()
        input_path = self.main_window.player.uri
        input_name = os.path.splitext(os.path.basename(input_path))[0]
        
        if format_type == "original":
            ext = os.path.splitext(input_path)[1]
        else:
            ext = f".{format_type}"
        
        quality = self.main_window.settings.get("quality", "1080p")
        video_codec = self.main_window.settings.get("video_codec", "H264")
        
        if format_type == "original":
            base_name = f"{input_name}.original"
        else:
            base_name = f"{input_name}.{quality}.{video_codec.lower()}"
        
        output_file = unique_output_path(base_name, ext, format_type)
        
        start = hmsms_to_seconds(
            self.main_window.start_h.get_value_as_int(), 
            self.main_window.start_m.get_value_as_int(), 
            self.main_window.start_s.get_value_as_int(),
            self.main_window.start_ms.get_value_as_int()
        )
        end = hmsms_to_seconds(
            self.main_window.end_h.get_value_as_int(), 
            self.main_window.end_m.get_value_as_int(), 
            self.main_window.end_s.get_value_as_int(),
            self.main_window.end_ms.get_value_as_int()
        )
        duration = end - start
        
        cmd = self.build_video_command(format_type, input_path, start, duration, output_file)
        
        if not cmd:
            return
        
        self._start_export_process(cmd, duration, output_file)
    
    # Build FFmpeg Command for Video
    def build_video_command(self, format_type, input_path, start, duration, output_file):
        video_filter = self.main_window.player.build_video_filter_for_ffmpeg()
        
        try:
            if format_type == "original":
                if video_filter:
                    cmd = [
                        "ffmpeg", "-y", "-ss", str(start), "-i", input_path, 
                        "-t", str(duration), "-vf", video_filter,
                        "-c:v", "libx264", "-preset", "fast", "-crf", "18"
                    ]
                    self._add_audio_params_to_cmd(cmd, format_type)
                else:
                    cmd = [
                        "ffmpeg", "-y", "-ss", str(start), "-i", input_path, 
                        "-t", str(duration), "-c", "copy"
                    ]
            else:
                cmd = [
                    "ffmpeg", "-y", "-ss", str(start), "-i", input_path, 
                    "-t", str(duration)
                ]
                
                video_codec = self.main_window.settings.get("video_codec", "H264")
                quality = self.main_window.settings.get("quality", "1080p")
                bitrate_type = self.main_window.settings.get("bitrate_type", "Auto")
                vbr_value = self.main_window.settings.get("vbr_value", 23)
                custom_bitrate = self.main_window.settings.get("custom_bitrate", "4000")
                
                if format_type == "wmv" and video_codec == "H265":
                    video_codec = "H264"
                    GLib.idle_add(
                        self.main_window.show_info_dialog,
                        "Codec Auto-Corrected",
                        f"WMV format requires H.264 codec.\n"
                        f"Automatically changed to H.264."
                    )
                
                if video_codec == "H264":
                    cmd.extend(["-c:v", "libx264", "-preset", "medium"])
                    if bitrate_type == "VBR":
                        cmd.extend(["-crf", str(vbr_value)])
                    elif bitrate_type == "Custom":
                        cmd.extend(["-b:v", f"{custom_bitrate}k"])
                    else:
                        if quality == "4K": cmd.extend(["-crf", "18"])
                        elif quality == "2K": cmd.extend(["-crf", "20"])
                        elif quality == "1080p": cmd.extend(["-crf", "23"])
                        elif quality == "720p": cmd.extend(["-crf", "23"])
                        elif quality == "480p": cmd.extend(["-crf", "23"])
                        else: cmd.extend(["-crf", "23"])
                            
                elif video_codec == "H265":
                    cmd.extend(["-c:v", "libx265", "-preset", "medium"])
                    if bitrate_type == "VBR":
                        cmd.extend(["-crf", str(vbr_value)])
                    elif bitrate_type == "Custom":
                        cmd.extend(["-b:v", f"{custom_bitrate}k"])
                    else:
                        if quality == "4K": cmd.extend(["-crf", "22"])
                        elif quality == "2K": cmd.extend(["-crf", "24"])
                        elif quality == "1080p": cmd.extend(["-crf", "26"])
                        elif quality == "720p": cmd.extend(["-crf", "26"])
                        elif quality == "480p": cmd.extend(["-crf", "26"])
                        else: cmd.extend(["-crf", "26"])
                            
                elif video_codec == "VP9":
                    cmd.extend(["-c:v", "libvpx-vp9"])
                    if bitrate_type == "VBR":
                        cmd.extend(["-crf", str(vbr_value), "-b:v", "0"])
                    elif bitrate_type == "Custom":
                        cmd.extend(["-b:v", f"{custom_bitrate}k"])
                    else:
                        if quality == "4K": cmd.extend(["-crf", "25", "-b:v", "0"])
                        elif quality == "2K": cmd.extend(["-crf", "28", "-b:v", "0"])
                        elif quality == "1080p": cmd.extend(["-crf", "30", "-b:v", "0"])
                        elif quality == "720p": cmd.extend(["-crf", "30", "-b:v", "0"])
                        elif quality == "480p": cmd.extend(["-crf", "30", "-b:v", "0"])
                        else: cmd.extend(["-crf", "30", "-b:v", "0"])
                            
                elif video_codec == "AV1":
                    cmd.extend(["-c:v", "libsvtav1", "-preset", "8"])
                    if bitrate_type == "VBR":
                        cmd.extend(["-crf", str(vbr_value)])
                    elif bitrate_type == "Custom":
                        cmd.extend(["-b:v", f"{custom_bitrate}k"])
                    else:
                        if quality == "4K": cmd.extend(["-crf", "25"])
                        elif quality == "2K": cmd.extend(["-crf", "28"])
                        elif quality == "1080p": cmd.extend(["-crf", "30"])
                        elif quality == "720p": cmd.extend(["-crf", "32"])
                        elif quality == "480p": cmd.extend(["-crf", "35"])
                        else: cmd.extend(["-crf", "30"])
                            
                elif video_codec == "MPEG-2":
                    cmd.extend(["-c:v", "mpeg2video", "-q:v", "5"])
                
                if quality != "Original":
                    if quality == "4K": scale_filter = "scale=3840:2160"
                    elif quality == "2K": scale_filter = "scale=2560:1440"
                    elif quality == "1080p": scale_filter = "scale=1920:1080"
                    elif quality == "720p": scale_filter = "scale=1280:720"
                    elif quality == "480p": scale_filter = "scale=854:480"
                    else: scale_filter = None
                    
                    if scale_filter:
                        if video_filter:
                            video_filter = f"{video_filter},{scale_filter}"
                        else:
                            video_filter = scale_filter
            
            if video_filter:
                cmd.extend(["-vf", video_filter])
            
            if format_type != "original" or video_filter:
                self._add_audio_params_to_cmd(cmd, format_type)
            
            cmd.append(output_file)
            
            print(f"FFmpeg command: {' '.join(cmd)}")
            return cmd
            
        except Exception as e:
            print(f"Error building FFmpeg command: {e}")
            self.main_window.show_error_dialog("Export Error", f"Error building command: {e}")
            return None
    
    # Add Audio Parameters to Command
    def _add_audio_params_to_cmd(self, cmd, format_type):
        video_audio_format = self.main_window.settings.get("video_audio_format", "AAC")
        video_audio_quality = self.main_window.settings.get("video_audio_quality", "192")
        
        if format_type == "webm":
            cmd.extend(["-c:a", "libopus", "-b:a", "192k"])
        elif format_type == "wmv":
            cmd.extend(["-c:a", "wmav2", "-b:a", "192k"])
        elif video_audio_format == "Copy Original":
            cmd.extend(["-c:a", "copy"])
        elif video_audio_format == "AAC":
            cmd.extend(["-c:a", "aac", "-b:a", f"{video_audio_quality}k"])
        elif video_audio_format == "MP3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", f"{video_audio_quality}k"])
        elif video_audio_format == "AC3":
            cmd.extend(["-c:a", "ac3", "-b:a", f"{video_audio_quality}k"])
        else:
            cmd.extend(["-c:a", "copy"])
    
    # Start Export Process in Thread
    def _start_export_process(self, cmd, duration, output_file):
        self.is_processing = True
        self.main_window.is_processing = True
        self.current_output_file = output_file
        
        GLib.idle_add(self.main_window.export_btn.set_sensitive, False)
        GLib.idle_add(self.main_window.abort_btn.set_sensitive, True)
        GLib.idle_add(self.main_window.status_label.set_text, f"Processing {os.path.basename(output_file)}...")
        GLib.idle_add(self.main_window.progress.set_fraction, 0.0)
        GLib.idle_add(self.main_window.percent_label.set_text, "0%")
        
        thread = threading.Thread(
            target=self._process_export,
            args=(cmd, duration, output_file, self.main_window.action_combo.get_active())
        )
        thread.daemon = True
        thread.start()
    
    # Manage Export Thread
    def _process_export(self, cmd, duration, output_file, action):
        success = self._run_ffmpeg_with_progress(cmd, duration, output_file)
        
        GLib.idle_add(self.main_window.export_btn.set_sensitive, True)
        GLib.idle_add(self.main_window.abort_btn.set_sensitive, False)
        
        if success and not self.abort_requested:
            GLib.idle_add(self._handle_post_export, action, output_file)
        elif not success and not self.abort_requested:
            GLib.idle_add(self.main_window.show_error_dialog, "Export Failed", 
                         "Video export failed. Please check the console for details.")
        
        self.is_processing = False
        self.main_window.is_processing = False
        self.current_output_file = None
        
        GLib.idle_add(self.main_window.status_label.set_text, "Ready")
        GLib.idle_add(self.main_window.progress.set_fraction, 0.0)
        GLib.idle_add(self.main_window.percent_label.set_text, "0%")
    
    # Run FFmpeg and Parse Progress
    def _run_ffmpeg_with_progress(self, cmd, total_duration, output_file):
        try:
            print("FFmpeg command:", " ".join(cmd))

            self.current_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, 
                                                   universal_newlines=True, bufsize=1)

            error_lines = []
            while True:
                if not self.is_processing or self.abort_requested:
                    try:
                        if self.current_process:
                            self.current_process.terminate()
                            self.current_process.wait(timeout=5)
                            self.current_process.kill()
                            self.current_process.wait(timeout=2)
                    except Exception:
                        pass
                    
                    GLib.idle_add(self.cleanup_incomplete_file, output_file)
                    return False

                line = self.current_process.stderr.readline()
                if not line and self.current_process.poll() is not None:
                    break
                
                if line:
                    progress = parse_ffmpeg_progress(line, total_duration)
                    if progress is not None:
                        percent = int(progress * 100)
                        GLib.idle_add(self.main_window.progress.set_fraction, progress)
                        GLib.idle_add(self.main_window.percent_label.set_text, f"{percent}%")
                    
                    if "error" in line.lower() or "failed" in line.lower():
                        error_lines.append(line.strip())
            
            ret = self.current_process.wait()
            
            if ret != 0:
                error_msg = "\n".join(error_lines[-5:]) if error_lines else "Unknown error occurred during processing."
                print(f"FFmpeg error: {error_msg}")
                GLib.idle_add(self.cleanup_incomplete_file, output_file)
                return False
            
            return True
        except Exception as e:
            print(f"Error running ffmpeg: {e}")
            GLib.idle_add(self.cleanup_incomplete_file, output_file)
            return False
        finally:
            self.current_process = None
    
    # Cleanup Incomplete File
    def cleanup_incomplete_file(self, output_file):
        def do_cleanup():
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    if os.path.exists(output_file):
                        file_size = os.path.getsize(output_file)
                        os.remove(output_file)
                        print(f"Removed incomplete file: {output_file} (was {file_size} bytes)")
                        return
                    else:
                        print(f"File does not exist: {output_file}")
                        return
                except Exception as e:
                    print(f"Cleanup attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)
                    else:
                        print(f"Failed to cleanup file after {max_attempts} attempts")
        
        if threading.current_thread() == threading.main_thread():
            do_cleanup()
        else:
            GLib.idle_add(do_cleanup)
    
    # Handle Post-Export Actions
    def _handle_post_export(self, action, output_file):
        if action == 0:
            self.main_window.show_info_dialog("Export Complete", f"File saved to:\n{output_file}")
        elif action == 1:
            output_dir = os.path.dirname(output_file)
            try:
                if os.name == 'nt':
                    os.startfile(output_dir)
                elif os.name == 'posix':
                    subprocess.Popen(['xdg-open', output_dir])
                self.main_window.show_info_dialog("Export Complete", f"File saved to:\n{output_file}")
            except Exception as e:
                print(f"Error opening folder: {e}")
                self.main_window.show_info_dialog("Export Complete", f"File saved to:\n{output_file}\n\nError opening folder: {e}")
        elif action == 2:
            Gtk.main_quit()
    
    # Abort Export Process
    def abort_export(self):
        if self.is_processing:
            self.abort_requested = True
            self.is_processing = False
            self.main_window.is_processing = False
            
            GLib.idle_add(self.main_window.status_label.set_text, "Aborting...")
            
            if self.current_process:
                try:
                    self.current_process.terminate()
                    time.sleep(0.5)
                    if self.current_process.poll() is None:
                        self.current_process.kill()
                except Exception:
                    pass
            
            if self.current_output_file:
                GLib.timeout_add(1000, self.delayed_cleanup, self.current_output_file)
    
    # Delayed Cleanup for Aborted Exports
    def delayed_cleanup(self, output_file):
        self.cleanup_incomplete_file(output_file)
        GLib.idle_add(self.main_window.status_label.set_text, "Ready")
        GLib.idle_add(self.main_window.progress.set_fraction, 0.0)
        GLib.idle_add(self.main_window.percent_label.set_text, "0%")
        GLib.idle_add(self.main_window.abort_btn.set_sensitive, False)
        GLib.idle_add(self.main_window.export_btn.set_sensitive, True)
        return False
