#!/usr/bin/env python3
import gi, os, subprocess, math, threading, time, re, signal
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gst, GLib, Gdk

Gst.init(None)

# تابع تشخیص نوع فایل - فقط ویدئو رو قبول میکنه
def get_file_type(file_path):
    """تشخیص نوع فایل (فقط ویدئو)"""
    try:
        # چک کردن وجود stream ویدئویی
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0",
            file_path
        ], capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            return "video"
        else:
            return None  # فایل ویدئویی نیست
    except Exception as e:
        print(f"Error detecting file type: {e}")
        return None  # در صورت خطا، فایل رو قبول نکن

# تابع بررسی فرمت فایل
def is_video_file(file_path):
    """بررسی می‌کند که فایل ویدئویی باشد"""
    video_extensions = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.flv', '.m4v', 
                       '.3gp', '.mpg', '.mpeg', '.m4v', '.ts', '.mts', '.m2ts'}
    ext = os.path.splitext(file_path)[1].lower()
    if ext in video_extensions:
        file_type = get_file_type(file_path)
        return file_type == "video"
    return False

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

def get_output_directory(format_type):
    home_dir = os.path.expanduser("~")
    if format_type in ["mp3", "aac", "wav"]:
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
    i = 2
    while True:
        candidate = f"{base_path}({i}){extension}"
        if not os.path.exists(candidate):
            return candidate
        i += 1


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent, current_settings):
        super().__init__(title="Export Settings", transient_for=parent, flags=0)
        self.set_default_size(450, 500)
        
        # ذخیره تنظیمات فعلی
        self.settings = current_settings.copy()
        
        # ایجاد رابط کاربری
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_border_width(10)
        
        # بخش فرمت
        format_frame = Gtk.Frame(label="Output Format")
        format_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        format_frame.add(format_box)
        
        # انتخاب فرمت
        format_label = Gtk.Label(label="Format:")
        format_box.pack_start(format_label, False, False, 0)
        
        self.format_combo = Gtk.ComboBoxText()
        formats = [
            ("MP4", "mp4"), ("MKV", "mkv"), ("WEBM", "webm"),
            ("AVI", "avi"), ("MOV", "mov"), ("WMV", "wmv"),
            ("MP3", "mp3"), ("AAC", "aac"), ("WAV", "wav"),
            ("Original (copy)", "original")
        ]
        for label, tag in formats:
            self.format_combo.append_text(label)
            if tag == current_settings.get("format", "mp4"):
                self.format_combo.set_active(formats.index((label, tag)))
        format_box.pack_start(self.format_combo, False, False, 0)
        
        # کیفیت
        quality_label = Gtk.Label(label="Quality:")
        format_box.pack_start(quality_label, False, False, 0)
        
        self.quality_combo = Gtk.ComboBoxText()
        format_box.pack_start(self.quality_combo, False, False, 0)
        
        # بیت ریت
        bitrate_label = Gtk.Label(label="Audio Bitrate (kbps):")
        format_box.pack_start(bitrate_label, False, False, 0)
        
        self.bitrate_spin = Gtk.SpinButton.new_with_range(64, 320, 32)
        self.bitrate_spin.set_value(current_settings.get("bitrate", 192))
        format_box.pack_start(self.bitrate_spin, False, False, 0)
        
        box.pack_start(format_frame, False, False, 0)
        
        # بخش تنظیمات پخش
        playback_frame = Gtk.Frame(label="Playback Settings")
        playback_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        playback_frame.add(playback_box)
        
        # تنظیمات seek
        seek_label = Gtk.Label(label="Seek Step (seconds):")
        playback_box.pack_start(seek_label, False, False, 0)
        
        self.seek_step = Gtk.SpinButton.new_with_range(0.1, 10, 0.1)
        self.seek_step.set_value(current_settings.get("seek_step", 1.0))
        self.seek_step.set_digits(1)
        playback_box.pack_start(self.seek_step, False, False, 0)
        
        # تنظیمات fine seek
        fine_seek_label = Gtk.Label(label="Fine Seek Step (seconds):")
        playback_box.pack_start(fine_seek_label, False, False, 0)
        
        self.fine_seek_step = Gtk.SpinButton.new_with_range(0.01, 1, 0.01)
        self.fine_seek_step.set_value(current_settings.get("fine_seek_step", 0.1))
        self.fine_seek_step.set_digits(2)
        playback_box.pack_start(self.fine_seek_step, False, False, 0)
        
        box.pack_start(playback_frame, False, False, 0)
        
        # بخش action بعد از پردازش
        action_frame = Gtk.Frame(label="After Export")
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        action_frame.add(action_box)
        
        action_label = Gtk.Label(label="After processing:")
        action_box.pack_start(action_label, False, False, 0)
        
        self.action_combo = Gtk.ComboBoxText()
        self.action_combo.append_text("No action")
        self.action_combo.append_text("Close App")
        self.action_combo.append_text("Open Output Folder")
        self.action_combo.set_active(current_settings.get("action", 0))
        action_box.pack_start(self.action_combo, False, False, 0)
        
        box.pack_start(action_frame, False, False, 0)
        
        # دکمه‌ها
        button_box = Gtk.Box(spacing=6)
        save_btn = Gtk.Button(label="Save Settings")
        cancel_btn = Gtk.Button(label="Cancel")
        
        save_btn.connect("clicked", self.on_save)
        cancel_btn.connect("clicked", self.on_cancel)
        
        button_box.pack_end(save_btn, False, False, 0)
        button_box.pack_end(cancel_btn, False, False, 0)
        
        box.pack_start(button_box, False, False, 0)
        
        # بروزرسانی اولیه کیفیت‌ها
        self.on_format_changed()
        self.format_combo.connect("changed", self.on_format_changed)
        
        self.show_all()
    
    def on_format_changed(self, widget=None):
        format_index = self.format_combo.get_active()
        format_tags = ["mp4", "mkv", "webm", "avi", "mov", "wmv", "mp3", "aac", "wav", "original"]
        
        if format_index >= 0 and format_index < len(format_tags):
            format_tag = format_tags[format_index]
            self.quality_combo.remove_all()
            
            if format_tag in ["mp4", "mkv", "webm", "avi", "mov", "wmv"]:
                self.quality_combo.append_text("4K")
                self.quality_combo.append_text("2K")
                self.quality_combo.append_text("1080p")
                self.quality_combo.append_text("720p")
                self.quality_combo.append_text("480p")
                self.quality_combo.append_text("Original")
                self.quality_combo.set_active(2)  # 1080p as default
                self.bitrate_spin.set_sensitive(True)
            elif format_tag in ["mp3", "aac"]:
                if format_tag == "mp3":
                    self.quality_combo.append_text("320 kbps")
                    self.quality_combo.append_text("256 kbps")
                    self.quality_combo.append_text("192 kbps")
                    self.quality_combo.append_text("128 kbps")
                else:  # aac
                    self.quality_combo.append_text("256 kbps")
                    self.quality_combo.append_text("192 kbps")
                    self.quality_combo.append_text("128 kbps")
                    self.quality_combo.append_text("96 kbps")
                self.quality_combo.set_active(1)
                self.bitrate_spin.set_sensitive(True)
            elif format_tag == "wav":
                self.quality_combo.append_text("24-bit HD")
                self.quality_combo.append_text("16-bit CD")
                self.quality_combo.append_text("8-bit")
                self.quality_combo.set_active(1)
                self.bitrate_spin.set_sensitive(False)
            else:  # original
                self.quality_combo.append_text("Same as source")
                self.quality_combo.set_active(0)
                self.bitrate_spin.set_sensitive(False)
    
    def on_save(self, widget):
        # ذخیره تنظیمات
        format_tags = ["mp4", "mkv", "webm", "avi", "mov", "wmv", "mp3", "aac", "wav", "original"]
        format_index = self.format_combo.get_active()
        
        if 0 <= format_index < len(format_tags):
            self.settings.update({
                "format": format_tags[format_index],
                "quality": self.quality_combo.get_active_text(),
                "bitrate": self.bitrate_spin.get_value(),
                "seek_step": self.seek_step.get_value(),
                "fine_seek_step": self.fine_seek_step.get_value(),
                "action": self.action_combo.get_active()
            })
        self.response(Gtk.ResponseType.OK)
    
    def on_cancel(self, widget):
        self.response(Gtk.ResponseType.CANCEL)
    
    def get_settings(self):
        return self.settings


class EmbeddedPlayer(Gtk.Box):
    def __init__(self, settings_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.playbin = Gst.ElementFactory.make("playbin", "player")
        self.duration = None
        self.uri = None
        self.is_seeking = False
        self.is_playing = False
        self.current_rotation = 0  # 0, 90, 180, 270
        self.flip_horizontal = False
        self.flip_vertical = False
        self.file_type = None  # 'audio' or 'video'
        self.settings_callback = settings_callback
        
        # Crop-related variables
        self.crop_mode = False
        self.crop_rect = None  # [x, y, width, height]
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.video_width = 0
        self.video_height = 0
        self.display_width = 0
        self.display_height = 0
        self.padding_x = 0
        self.padding_y = 0

        self.videoflip = Gst.ElementFactory.make("videoflip", "videoflip")
        self.videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
        self.vsink = Gst.ElementFactory.make("gtksink", "gtksink")

        self.use_gtksink = False
        
        # Create main container for video
        self.video_container = Gtk.Box()
        self.video_container.set_size_request(600, 350)  # کاهش بیشتر سایز
        
        # Create overlay for video and audio message
        self.overlay = Gtk.Overlay()
        
        # Drawing area for crop rectangle
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_visible(False)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | 
                                    Gdk.EventMask.BUTTON_RELEASE_MASK |
                                    Gdk.EventMask.POINTER_MOTION_MASK)
        
        # Label for invalid file message
        self.invalid_file_label = Gtk.Label()
        self.invalid_file_label.set_visible(False)
        self.invalid_file_label.set_justify(Gtk.Justification.CENTER)
        self.invalid_file_label.set_line_wrap(True)
        
        # Pack everything
        self.video_container.pack_start(self.overlay, True, True, 0)
        self.overlay.add_overlay(self.drawing_area)
        self.overlay.add_overlay(self.invalid_file_label)
        self.pack_start(self.video_container, True, True, 0)

        if not (self.videoflip and self.videoconvert and self.vsink):
            lbl = Gtk.Label(label="Required GStreamer sinks/converters not available.")
            lbl.set_justify(Gtk.Justification.CENTER)
            self.overlay.add(lbl)
            lbl.show()
        else:
            self.videobin = Gst.Bin.new("video-bin")
            self.videobin.add(self.videoflip)
            self.videobin.add(self.videoconvert)
            self.videobin.add(self.vsink)
            self.videoflip.link(self.videoconvert)
            self.videoconvert.link(self.vsink)

            sink_pad = self.videoflip.get_static_pad("sink")
            ghost = Gst.GhostPad.new("sink", sink_pad)
            self.videobin.add_pad(ghost)
            self.playbin.set_property("video-sink", self.videobin)

            try:
                self.video_widget = self.vsink.get_property("widget")
                if self.video_widget:
                    self.overlay.add(self.video_widget)
                    self.video_widget.show()
                    self.use_gtksink = True
                    # Connect to size-allocate to get video display dimensions
                    self.video_widget.connect("size-allocate", self.on_video_size_allocate)
            except Exception as e:
                print(f"Error getting gtksink widget: {e}")
                # Fallback: create a label if gtksink fails
                lbl = Gtk.Label(label="Video preview not available. Using external window.")
                lbl.set_justify(Gtk.Justification.CENTER)
                self.overlay.add(lbl)
                lbl.show()

        # --- UI controls setup ---
        controls_container = Gtk.Box(spacing=8)
        self.pack_start(controls_container, False, False, 0)

        main_controls = Gtk.Box(spacing=4)
        self.play_pause_btn = Gtk.Button(label="Play")
        self.play_pause_btn.set_size_request(70, -1)
        
        # دکمه‌های کنترل پیشرفته
        self.fine_minus_btn = Gtk.Button(label="−0.1s")
        self.minus_btn = Gtk.Button(label="−1s")
        self.plus_btn = Gtk.Button(label="+1s")
        self.fine_plus_btn = Gtk.Button(label="+0.1s")
        
        self.in_btn = Gtk.Button(label="Set In")
        self.out_btn = Gtk.Button(label="Set Out")

        for w in (self.play_pause_btn, self.fine_minus_btn, self.minus_btn, 
                  self.plus_btn, self.fine_plus_btn, self.in_btn, self.out_btn):
            main_controls.pack_start(w, False, False, 0)

        # Container for video controls
        self.video_controls_box = Gtk.Box(spacing=4)
        self.rotate_left_btn = Gtk.Button(label="↶ 90°")
        self.rotate_right_btn = Gtk.Button(label="↷ 90°")
        self.flip_horizontal_btn = Gtk.Button(label="↔ Flip H")
        self.flip_vertical_btn = Gtk.Button(label="↕ Flip V")
        self.reset_rotation_btn = Gtk.Button(label="⟲ Reset")
        
        # Crop controls
        self.crop_btn = Gtk.ToggleButton(label="Crop Mode")
        self.crop_preset_combo = Gtk.ComboBoxText()
        self.crop_preset_combo.append_text("Free")
        self.crop_preset_combo.append_text("1:1")
        self.crop_preset_combo.append_text("16:9")
        self.crop_preset_combo.append_text("9:16")
        self.crop_preset_combo.append_text("4:3")
        self.crop_preset_combo.set_active(0)

        for w in (self.rotate_left_btn, self.rotate_right_btn,
                  self.flip_horizontal_btn, self.flip_vertical_btn, 
                  self.reset_rotation_btn, self.crop_btn, self.crop_preset_combo):
            self.video_controls_box.pack_start(w, False, False, 0)

        controls_container.pack_start(main_controls, True, True, 0)
        controls_container.pack_start(self.video_controls_box, False, False, 0)

        seek_row = Gtk.Box(spacing=6)
        self.pos_label = Gtk.Label(label="00:00:00.000")
        self.seek = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.001)
        self.seek.set_draw_value(False)
        self.duration_label = Gtk.Label(label="00:00:00.000")
        seek_row.pack_start(self.pos_label, False, False, 0)
        seek_row.pack_start(self.seek, True, True, 0)
        seek_row.pack_start(self.duration_label, False, False, 0)
        self.pack_start(seek_row, False, False, 0)

        # --- Connect buttons ---
        self.play_pause_btn.connect("clicked", self.on_play_pause)
        self.minus_btn.connect("clicked", lambda w: self.seek_delta(-self.get_seek_step()))
        self.plus_btn.connect("clicked", lambda w: self.seek_delta(self.get_seek_step()))
        self.fine_minus_btn.connect("clicked", lambda w: self.seek_delta(-self.get_fine_seek_step()))
        self.fine_plus_btn.connect("clicked", lambda w: self.seek_delta(self.get_fine_seek_step()))
        self.rotate_left_btn.connect("clicked", lambda w: self.rotate_video("left"))
        self.rotate_right_btn.connect("clicked", lambda w: self.rotate_video("right"))
        self.flip_horizontal_btn.connect("clicked", lambda w: self.rotate_video("horizontal"))
        self.flip_vertical_btn.connect("clicked", lambda w: self.rotate_video("vertical"))
        self.reset_rotation_btn.connect("clicked", lambda w: self.rotate_video("reset"))
        self.crop_btn.connect("toggled", self.on_crop_mode_toggled)
        self.crop_preset_combo.connect("changed", self.on_crop_preset_changed)

        self.seek.connect("button-press-event", self.on_seek_press)
        self.seek.connect("button-release-event", self.on_seek_release)
        self.seek.connect("value-changed", self.on_seek_value_changed)
        
        # Connect drawing area events
        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.connect("button-press-event", self.on_button_press)
        self.drawing_area.connect("button-release-event", self.on_button_release)
        self.drawing_area.connect("motion-notify-event", self.on_motion_notify)

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_bus_message)
        GLib.timeout_add(100, self.update_position)

    def get_seek_step(self):
        settings = self.settings_callback()
        return settings.get("seek_step", 1.0)

    def get_fine_seek_step(self):
        settings = self.settings_callback()
        return settings.get("fine_seek_step", 0.1)

    def on_video_size_allocate(self, widget, allocation):
        """Called when video widget gets its size"""
        self.display_width = allocation.width
        self.display_height = allocation.height
        self.calculate_padding()

    def calculate_padding(self):
        """Calculate padding for letterbox/pillarbox display"""
        if not self.video_width or not self.video_height or not self.display_width or not self.display_height:
            return
        
        video_ratio = self.video_width / self.video_height
        display_ratio = self.display_width / self.display_height
        
        if video_ratio > display_ratio:
            # Letterbox (black bars on top and bottom)
            scaled_height = int(self.display_width / video_ratio)
            self.padding_y = (self.display_height - scaled_height) // 2
            self.padding_x = 0
        else:
            # Pillarbox (black bars on sides)
            scaled_width = int(self.display_height * video_ratio)
            self.padding_x = (self.display_width - scaled_width) // 2
            self.padding_y = 0

    # --- Crop-related methods ---
    def on_crop_mode_toggled(self, widget):
        if self.file_type != "video":
            widget.set_active(False)
            return
            
        self.crop_mode = widget.get_active()
        self.drawing_area.set_visible(self.crop_mode)
        
        if not self.crop_mode:
            # Reset crop when exiting crop mode
            self.crop_rect = None
            self.drawing_area.queue_draw()

    def on_crop_preset_changed(self, widget):
        if self.file_type != "video":
            return
        if self.crop_rect and self.crop_mode:
            self.apply_aspect_ratio()

    def apply_aspect_ratio(self):
        if not self.crop_rect:
            return
            
        preset = self.crop_preset_combo.get_active_text()
        if preset == "Free":
            return
            
        x, y, w, h = self.crop_rect
        
        if preset == "1:1":
            # مربع - کوچکترین بعد را بگیر
            size = min(abs(w), abs(h))
            if w < 0:
                w = -size
            else:
                w = size
            if h < 0:
                h = -size
            else:
                h = size
                
        elif preset == "16:9":
            # واید اسکرین
            ratio = 16.0 / 9.0
            if abs(w) > abs(h) * ratio:
                # عرض زیاد است
                new_w = abs(h) * ratio
                if w < 0:
                    w = -new_w
                else:
                    w = new_w
            else:
                # ارتفاع زیاد است
                new_h = abs(w) / ratio
                if h < 0:
                    h = -new_h
                else:
                    h = new_h
                    
        elif preset == "9:16":
            # پرتره
            ratio = 9.0 / 16.0
            if abs(w) > abs(h) * ratio:
                # عرض زیاد است
                new_w = abs(h) * ratio
                if w < 0:
                    w = -new_w
                else:
                    w = new_w
            else:
                # ارتفاع زیاد است
                new_h = abs(w) / ratio
                if h < 0:
                    h = -new_h
                else:
                    h = new_h
                    
        elif preset == "4:3":
            # استاندارد
            ratio = 4.0 / 3.0
            if abs(w) > abs(h) * ratio:
                # عرض زیاد است
                new_w = abs(h) * ratio
                if w < 0:
                    w = -new_w
                else:
                    w = new_w
            else:
                # ارتفاع زیاد است
                new_h = abs(w) / ratio
                if h < 0:
                    h = -new_h
                else:
                    h = new_h
        
        self.crop_rect = [x, y, w, h]
        self.drawing_area.queue_draw()

    def on_draw(self, widget, cr):
        if self.crop_rect:
            # Draw semi-transparent red rectangle
            cr.set_source_rgba(1, 0, 0, 0.3)
            x, y, w, h = self.crop_rect
            # Normalize coordinates for drawing
            draw_x = x if w >= 0 else x + w
            draw_y = y if h >= 0 else y + h
            draw_w = abs(w)
            draw_h = abs(h)
            cr.rectangle(draw_x, draw_y, draw_w, draw_h)
            cr.fill_preserve()
            
            # Draw red border
            cr.set_source_rgba(1, 0, 0, 1)
            cr.set_line_width(2)
            cr.stroke()

    def on_button_press(self, widget, event):
        if self.file_type != "video":
            return
        if self.crop_mode and event.button == 1:  # Left click
            self.dragging = True
            self.start_x = event.x
            self.start_y = event.y
            self.crop_rect = [event.x, event.y, 0, 0]
            self.drawing_area.queue_draw()

    def on_motion_notify(self, widget, event):
        if self.file_type != "video":
            return
        if self.crop_mode and self.dragging and self.crop_rect:
            self.crop_rect[2] = event.x - self.start_x
            self.crop_rect[3] = event.y - self.start_y
            self.apply_aspect_ratio()  # Apply aspect ratio while dragging
            self.drawing_area.queue_draw()

    def on_button_release(self, widget, event):
        if self.file_type != "video":
            return
        if self.crop_mode and event.button == 1:
            self.dragging = False
            # Ensure minimum size
            if abs(self.crop_rect[2]) < 10 or abs(self.crop_rect[3]) < 10:
                self.crop_rect = None
            self.drawing_area.queue_draw()

    def get_crop_filter(self):
        """Generate ffmpeg crop filter string from current crop rectangle"""
        if not self.crop_rect or not self.crop_mode or self.file_type != "video":
            return None
        
        # Get video dimensions
        if not self.video_width or not self.video_height:
            return None
        
        # Get drawing area dimensions
        da_width = self.drawing_area.get_allocated_width()
        da_height = self.drawing_area.get_allocated_height()
        
        if da_width <= 0 or da_height <= 0:
            return None
        
        # Normalize crop coordinates
        x1 = self.crop_rect[0] if self.crop_rect[2] >= 0 else self.crop_rect[0] + self.crop_rect[2]
        y1 = self.crop_rect[1] if self.crop_rect[3] >= 0 else self.crop_rect[1] + self.crop_rect[3]
        x2 = x1 + abs(self.crop_rect[2])
        y2 = y1 + abs(self.crop_rect[3])
        
        # Adjust for padding (letterbox/pillarbox)
        display_x1 = self.padding_x
        display_y1 = self.padding_y
        display_x2 = self.display_width - self.padding_x
        display_y2 = self.display_height - self.padding_y
        
        # Ensure crop is within the actual video area (not in padding)
        x1 = max(x1, display_x1)
        y1 = max(y1, display_y1)
        x2 = min(x2, display_x2)
        y2 = min(y2, display_y2)
        
        # Calculate scale factors
        scale_x = self.video_width / (display_x2 - display_x1)
        scale_y = self.video_height / (display_y2 - display_y1)
        
        # Convert coordinates from display to original video
        video_x = int((x1 - display_x1) * scale_x)
        video_y = int((y1 - display_y1) * scale_y)
        video_w = int((x2 - x1) * scale_x)
        video_h = int((y2 - y1) * scale_y)
        
        # Ensure coordinates are within video bounds and even numbers (required by some codecs)
        video_x = max(0, min(video_x, self.video_width - 2))
        video_y = max(0, min(video_y, self.video_height - 2))
        video_w = min(video_w, self.video_width - video_x)
        video_h = min(video_h, self.video_height - video_y)
        
        # Ensure even dimensions (required by some codecs)
        video_w = video_w & ~1  # Make even
        video_h = video_h & ~1  # Make even
        
        # Ensure minimum size
        if video_w <= 0 or video_h <= 0:
            return None
        
        return f"crop={video_w}:{video_h}:{video_x}:{video_y}"

    def get_video_size(self):
        """Get original video dimensions"""
        if not self.uri:
            return None, None
        
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "csv=p=0",
                self.uri
            ], capture_output=True, text=True, check=True)
            
            width, height = map(int, result.stdout.strip().split(','))
            self.video_width = width
            self.video_height = height
            # Recalculate padding with new video dimensions
            GLib.idle_add(self.calculate_padding)
            return width, height
        except Exception as e:
            print(f"Error getting video size: {e}")
            return None, None

    def clear_crop(self):
        """Clear current crop selection"""
        self.crop_rect = None
        self.drawing_area.queue_draw()

    # --- Existing methods with crop integration ---
    def _compute_videoflip_method(self):
        rot_map = {0:0, 90:1, 180:2, 270:3}
        r = self.current_rotation % 360
        if r not in rot_map:
            r = 0
        if not self.flip_horizontal and not self.flip_vertical:
            return rot_map[r]
        if self.flip_horizontal and self.flip_vertical:
            map_both = {0:2, 90:3, 180:0, 270:1}
            return map_both.get(r, 2)
        if self.flip_horizontal and not self.flip_vertical:
            map_h = {0:4, 90:7, 180:5, 270:6}
            return map_h.get(r, 4)
        if not self.flip_horizontal and self.flip_vertical:
            map_v = {0:5, 90:6, 180:4, 270:7}
            return map_v.get(r, 5)
        return 0

    def apply_video_filters(self):
        """Apply videoflip method in place"""
        if not getattr(self, "videoflip", None) or self.file_type != "video":
            return
        method = self._compute_videoflip_method()
        try:
            self.videoflip.set_property("method", method)
        except Exception as e:
            print(f"Error setting videoflip method: {e}")

    def rotate_video(self, rotation_type):
        """Rotate or flip video and refresh frame if paused"""
        if not self.uri or self.file_type != "video":
            return
        if rotation_type == "left":
            self.current_rotation = (self.current_rotation - 90) % 360
        elif rotation_type == "right":
            self.current_rotation = (self.current_rotation + 90) % 360
        elif rotation_type == "horizontal":
            self.flip_horizontal = not self.flip_horizontal
        elif rotation_type == "vertical":
            self.flip_vertical = not self.flip_vertical
        elif rotation_type == "reset":
            self.current_rotation = 0
            self.flip_horizontal = False
            self.flip_vertical = False
            self.clear_crop()

        # apply new flip method
        self.apply_video_filters()

        # if paused, force frame refresh so user sees rotation immediately
        if not self.is_playing:
            pos = self.query_position()
            if pos is not None:
                self.seek_to(pos)

    def set_file(self, path):
        if not path:
            return
        
        # Stop and reset current playback
        self.playbin.set_state(Gst.State.NULL)
        
        # بررسی اینکه فایل ویدئویی معتبر است
        if not is_video_file(path):
            print(f"Invalid video file: {path}")
            # نمایش پیام خطا
            if self.use_gtksink:
                self.video_widget.hide()
            
            self.invalid_file_label.set_text(
                f"Invalid video file!\n\n"
                f"Please select a valid video file.\n"
                f"Supported formats: MP4, MKV, AVI, MOV, WebM, WMV, etc."
            )
            self.invalid_file_label.show()
            self.drawing_area.set_visible(False)
            self.video_controls_box.hide()
            
            # Reset UI elements
            self.pos_label.set_text("00:00:00.000")
            self.duration_label.set_text("00:00:00.000")
            self.seek.set_range(0.0, 1.0)
            self.seek.set_value(0.0)
            return
        
        # تشخیص نوع فایل
        self.file_type = "video"  # فقط ویدئو قبول میکنیم
        print(f"File type detected: {self.file_type}")
        
        uri = Gst.filename_to_uri(path)
        self.playbin.set_property("uri", uri)
        self.uri = path
        self.duration = None
        self.is_seeking = False
        self.is_playing = False
        self.play_pause_btn.set_label("Play")
        self.current_rotation = 0
        self.flip_horizontal = False
        self.flip_vertical = False
        self.clear_crop()
        
        # حالت ویدئو
        print("Setting up video mode")
        self.get_video_size()
        if self.use_gtksink:
            self.video_widget.show()
        self.invalid_file_label.hide()
        self.drawing_area.set_visible(False)
        
        # نمایش کنترل‌های ویدئو
        self.video_controls_box.show_all()
        
        # Reset video filters
        if getattr(self, "videoflip", None):
            try:
                self.videoflip.set_property("method", 0)
            except Exception:
                pass
        
        # Reset UI elements
        self.pos_label.set_text("00:00:00.000")
        self.duration_label.set_text("00:00:00.000")
        self.seek.set_range(0.0, 1.0)
        self.seek.set_value(0.0)
        
        # Set to paused state ready for playback
        self.playbin.set_state(Gst.State.PAUSED)

    def on_play_pause(self, widget):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        self.playbin.set_state(Gst.State.PLAYING)
        self.is_playing = True
        self.play_pause_btn.set_label("Pause")

    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)
        self.is_playing = False
        self.play_pause_btn.set_label("Play")

    def query_duration(self):
        success, dur = self.playbin.query_duration(Gst.Format.TIME)
        if success:
            self.duration = dur / Gst.SECOND
            return self.duration

    def query_position(self):
        success, pos = self.playbin.query_position(Gst.Format.TIME)
        return pos / Gst.SECOND if success else None

    def update_position(self):
        if not self.is_seeking:
            pos = self.query_position()
            if self.duration is None:
                self.query_duration()
            if self.duration:
                self.seek.set_range(0.0, self.duration)
            if pos is not None:
                self.seek.set_value(pos)
                self.pos_label.set_text(hmsms_str(pos))
                if self.duration:
                    self.duration_label.set_text(hmsms_str(self.duration))
        return True

    def on_seek_press(self, widget, event):
        self.is_seeking = True

    def on_seek_release(self, widget, event):
        self.is_seeking = False
        val = self.seek.get_value()
        self.seek_to(val)

    def on_seek_value_changed(self, widget):
        if self.is_seeking:
            val = self.seek.get_value()
            self.pos_label.set_text(hmsms_str(val))

    def seek_to(self, seconds):
        if seconds < 0: seconds = 0
        if self.duration: seconds = min(seconds, self.duration)
        try:
            self.playbin.seek_simple(Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                int(seconds * Gst.SECOND))
        except Exception as e:
            print(f"Seek error: {e}")

    def seek_delta(self, delta):
        pos = self.query_position()
        if pos is None: return
        self.seek_to(pos + delta)

    def on_bus_message(self, bus, msg):
        """Handle GStreamer bus messages"""
        if msg.type == Gst.MessageType.EOS:
            # End of stream
            self.playbin.set_state(Gst.State.PAUSED)
            self.is_playing = False
            self.play_pause_btn.set_label("Play")
            # Seek to beginning
            self.seek_to(0)
        elif msg.type == Gst.MessageType.ERROR:
            # Error handling
            err, dbg = msg.parse_error()
            print("GStreamer error:", err, dbg)
            self.playbin.set_state(Gst.State.NULL)
            self.is_playing = False
            self.play_pause_btn.set_label("Play")
        elif msg.type == Gst.MessageType.WARNING:
            # Warning handling
            warn, dbg = msg.parse_warning()
            print("GStreamer warning:", warn, dbg)
        elif msg.type == Gst.MessageType.STATE_CHANGED:
            # State change handling
            old_state, new_state, pending_state = msg.parse_state_changed()
            if msg.src == self.playbin:
                print(f"Pipeline state changed: {old_state} -> {new_state}")


class NamaCut(Gtk.Window):
    def __init__(self):
        super().__init__(title="NamaCut - Video Cutter v1.3")
        self.set_default_size(800, 550)  # ارتفاع کمتر
        self.connect("destroy", Gtk.main_quit)
        
        # تنظیمات پیشفرض
        self.settings = {
            "format": "mp4",
            "quality": "1080p",
            "bitrate": 192,
            "seek_step": 1.0,
            "fine_seek_step": 0.1,
            "action": 0
        }
        
        # Enable drag and drop
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.connect("drag-data-received", self.on_drag_data_received)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_border_width(6)
        self.add(vbox)

        # نوار ابزار بالا
        toolbar = Gtk.Box(spacing=6)
        
        # آیکون برنامه
        try:
            app_icon = Gtk.Image.new_from_icon_name("avidemux", Gtk.IconSize.DND)
        except:
            try:
                app_icon = Gtk.Image.new_from_icon_name("video-x-generic", Gtk.IconSize.DND)
            except:
                app_icon = Gtk.Image.new_from_icon_name("gtk-media-play", Gtk.IconSize.DND)
        
        toolbar.pack_start(app_icon, False, False, 0)
        
        # عنوان برنامه
        title_label = Gtk.Label()
        title_label.set_markup("<b>NamaCut</b>")
        toolbar.pack_start(title_label, False, False, 6)
        
        # Drag and drop hint
        drop_hint = Gtk.Label()
        drop_hint.set_markup("<span foreground='gray'><i>Drag & drop video files here</i></span>")
        toolbar.pack_start(drop_hint, False, False, 0)
        
        toolbar.pack_start(Gtk.Label(), True, True, 0)  # Spacer
        
        # دکمه About
        self.about_btn = Gtk.Button()
        self.about_btn.set_tooltip_text("About")
        about_icon = Gtk.Image.new_from_icon_name("help-about-symbolic", Gtk.IconSize.BUTTON)
        self.about_btn.set_image(about_icon)
        self.about_btn.connect("clicked", self.on_about_clicked)
        toolbar.pack_start(self.about_btn, False, False, 0)
        
        # دکمه تنظیمات
        self.settings_btn = Gtk.Button()
        self.settings_btn.set_tooltip_text("Export Settings")
        settings_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        self.settings_btn.set_image(settings_icon)
        self.settings_btn.connect("clicked", self.on_settings_clicked)
        toolbar.pack_start(self.settings_btn, False, False, 0)
        
        vbox.pack_start(toolbar, False, False, 0)

        # Separator
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(sep1, False, False, 4)

        top = Gtk.Box(spacing=6)
        self.filechooser = Gtk.FileChooserButton(title="Select video file", action=Gtk.FileChooserAction.OPEN)
        self.filechooser.set_filter(self.file_filter())
        top.pack_start(self.filechooser, True, True, 0)

        self.duration_label = Gtk.Label(label="Duration: Unknown")
        top.pack_start(self.duration_label, False, False, 0)

        vbox.pack_start(top, False, False, 0)

        self.player = EmbeddedPlayer(self.get_settings)
        vbox.pack_start(self.player, True, True, 0)

        self.player.in_btn.connect("clicked", self._set_in)
        self.player.out_btn.connect("clicked", self._set_out)

        # بخش زمان‌بندی با میلی‌ثانیه
        time_grid = Gtk.Grid(column_spacing=6, row_spacing=4)
        vbox.pack_start(time_grid, False, False, 0)
        
        # ردیف Start
        time_grid.attach(Gtk.Label(label="Start:"), 0, 0, 1, 1)
        
        start_box = Gtk.Box(spacing=2)
        self.start_h = Gtk.SpinButton.new_with_range(0, 99, 1)
        self.start_h.set_size_request(45, -1)
        self.start_m = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.start_m.set_size_request(45, -1)
        self.start_s = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.start_s.set_size_request(45, -1)
        self.start_ms = Gtk.SpinButton.new_with_range(0, 999, 1)
        self.start_ms.set_size_request(55, -1)
        
        start_box.pack_start(self.start_h, False, False, 0)
        start_box.pack_start(Gtk.Label(label="h"), False, False, 0)
        start_box.pack_start(self.start_m, False, False, 0)
        start_box.pack_start(Gtk.Label(label="m"), False, False, 0)
        start_box.pack_start(self.start_s, False, False, 0)
        start_box.pack_start(Gtk.Label(label="s"), False, False, 0)
        start_box.pack_start(self.start_ms, False, False, 0)
        start_box.pack_start(Gtk.Label(label="ms"), False, False, 0)
        
        time_grid.attach(start_box, 1, 0, 1, 1)
        
        # ردیف End
        time_grid.attach(Gtk.Label(label="End:"), 0, 1, 1, 1)
        
        end_box = Gtk.Box(spacing=2)
        self.end_h = Gtk.SpinButton.new_with_range(0, 99, 1)
        self.end_h.set_size_request(45, -1)
        self.end_m = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.end_m.set_size_request(45, -1)
        self.end_s = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.end_s.set_size_request(45, -1)
        self.end_ms = Gtk.SpinButton.new_with_range(0, 999, 1)
        self.end_ms.set_size_request(55, -1)
        
        end_box.pack_start(self.end_h, False, False, 0)
        end_box.pack_start(Gtk.Label(label="h"), False, False, 0)
        end_box.pack_start(self.end_m, False, False, 0)
        end_box.pack_start(Gtk.Label(label="m"), False, False, 0)
        end_box.pack_start(self.end_s, False, False, 0)
        end_box.pack_start(Gtk.Label(label="s"), False, False, 0)
        end_box.pack_start(self.end_ms, False, False, 0)
        end_box.pack_start(Gtk.Label(label="ms"), False, False, 0)
        
        time_grid.attach(end_box, 1, 1, 1, 1)

        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(sep2, False, False, 4)

        # دکمه‌های اصلی
        actions = Gtk.Box(spacing=6)
        self.trim_btn = Gtk.Button(label="Export")
        self.trim_btn.get_style_context().add_class("suggested-action")
        self.abort_btn = Gtk.Button(label="Abort")
        self.abort_btn.set_sensitive(False)
        self.quit_btn = Gtk.Button(label="Quit")

        actions.pack_end(self.quit_btn, False, False, 0)
        actions.pack_end(self.abort_btn, False, False, 0)
        actions.pack_end(self.trim_btn, False, False, 0)

        vbox.pack_start(actions, False, False, 0)

        self.status = Gtk.Label(label="")
        vbox.pack_start(self.status, False, False, 0)

        progress_box = Gtk.Box(spacing=6)
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        self.percent_label = Gtk.Label(label="0%")
        self.percent_label.set_size_request(40, -1)

        progress_box.pack_start(self.progress, True, True, 0)
        progress_box.pack_start(self.percent_label, False, False, 0)
        vbox.pack_start(progress_box, False, False, 4)

        self.current_process = None
        self.is_processing = False

        self.filechooser.connect("file-set", self.on_file_selected)
        self.trim_btn.connect("clicked", self.on_trim)
        self.abort_btn.connect("clicked", self.on_abort)
        self.quit_btn.connect("clicked", lambda w: Gtk.main_quit())

    def on_about_clicked(self, btn):
        about = Gtk.AboutDialog(transient_for=self, modal=True)
        about.set_program_name("NamaCut")
        about.set_version("1.3")
        about.set_comments("Video Editor and Cutter")
        about.set_authors(["Pourdaryaei"])
        about.set_website("https://pourdaryaei.ir")
        # use the installed icon name if available
        try:
            about.set_logo_icon_name("avidemux")
        except Exception:
            pass
        about.run()
        about.destroy()

    def get_settings(self):
        return self.settings

    def on_settings_clicked(self, widget):
        dialog = SettingsDialog(self, self.settings)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            self.settings = dialog.get_settings()
            print("Settings saved:", self.settings)
        
        dialog.destroy()

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        """Handle drag and drop files"""
        if data.get_uris():
            uri = data.get_uris()[0]
            file_path = uri.replace('file://', '')
            file_path = GLib.filename_from_uri(uri)[0] if uri.startswith('file://') else file_path
            
            print(f"File dropped: {file_path}")
            
            # بررسی اینکه فایل ویدئویی معتبر است
            if is_video_file(file_path):
                self.filechooser.set_filename(file_path)
                self.on_file_selected(self.filechooser)
            else:
                # نمایش پیام خطا
                self.show_error_dialog(
                    "Invalid Video File",
                    "Please drop a valid video file.\n\n"
                    "Supported formats:\n"
                    "MP4, MKV, WebM, AVI, MOV, WMV, FLV, etc."
                )

    def show_error_dialog(self, title, message):
        """نمایش دیالوگ خطا با فرمت بهتر"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def show_info_dialog(self, title, message):
        """نمایش دیالوگ اطلاعات با فرمت بهتر"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    # ---------------------------
    # In/out helpers with milliseconds
    # ---------------------------
    def _set_in(self, *args):
        pos = self.player.query_position()
        if pos is not None:
            end_time = hmsms_to_seconds(
                self.end_h.get_value_as_int(), 
                self.end_m.get_value_as_int(), 
                self.end_s.get_value_as_int(),
                self.end_ms.get_value_as_int()
            )
            if pos > end_time:
                self.show_error_dialog("Invalid In Point", "In point can't be after Out point!")
                return
            h, m, s, ms = seconds_to_hmsms(pos)
            self.start_h.set_value(h)
            self.start_m.set_value(m)
            self.start_s.set_value(s)
            self.start_ms.set_value(ms)

    def _set_out(self, *args):
        pos = self.player.query_position()
        if pos is not None:
            start_time = hmsms_to_seconds(
                self.start_h.get_value_as_int(), 
                self.start_m.get_value_as_int(), 
                self.start_s.get_value_as_int(),
                self.start_ms.get_value_as_int()
            )
            if pos < start_time:
                self.show_error_dialog("Invalid Out Point", "Out point can't be before In point!")
                return
            h, m, s, ms = seconds_to_hmsms(pos)
            self.end_h.set_value(h)
            self.end_m.set_value(m)
            self.end_s.set_value(s)
            self.end_ms.set_value(ms)

    def validate_times(self):
        start = hmsms_to_seconds(
            self.start_h.get_value_as_int(), 
            self.start_m.get_value_as_int(), 
            self.start_s.get_value_as_int(),
            self.start_ms.get_value_as_int()
        )
        end = hmsms_to_seconds(
            self.end_h.get_value_as_int(), 
            self.end_m.get_value_as_int(), 
            self.end_s.get_value_as_int(),
            self.end_ms.get_value_as_int()
        )
        if start >= end:
            return False, "Start must be less than End."
        return True, ""

    def get_selected_format(self):
        return self.settings.get("format", "mp4")

    def file_filter(self):
        f = Gtk.FileFilter()
        f.set_name("Video files")
        # فقط فایل‌های ویدئویی
        for p in ("*.mp4", "*.mkv", "*.webm", "*.avi", "*.mov", "*.wmv", "*.flv", "*.m4v", "*.3gp", "*.mpg", "*.mpeg", "*.ts", "*.mts", "*.m2ts"):
            f.add_pattern(p)
        f.add_mime_type("video/*")
        return f

    def on_file_selected(self, chooser):
        path = chooser.get_filename()
        if not path: 
            return
        
        # بررسی اینکه فایل ویدئویی معتبر است
        if not is_video_file(path):
            self.show_error_dialog(
                "Invalid Video File", 
                "Please select a valid video file.\n\n"
                "The file either is not a video or is corrupted."
            )
            return
        
        # Reset player with new file
        self.player.set_file(path)
        
        try:
            out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", path], text=True, stderr=subprocess.DEVNULL)
            durf = float(out.strip())
            h, m, s, ms = seconds_to_hmsms(durf)
            self.duration_label.set_text(f"Duration: {h:02d}:{m:02d}:{s:02d}.{ms:03d}")
            self.start_h.set_value(0); self.start_m.set_value(0); self.start_s.set_value(0); self.start_ms.set_value(0)
            self.end_h.set_value(h); self.end_m.set_value(m); self.end_s.set_value(s); self.end_ms.set_value(ms)
        except Exception:
            self.duration_label.set_text("Duration: Unknown")
            # Reset time inputs on error
            self.start_h.set_value(0); self.start_m.set_value(0); self.start_s.set_value(0); self.start_ms.set_value(0)
            self.end_h.set_value(0); self.end_m.set_value(0); self.end_s.set_value(0); self.end_ms.set_value(0)

    # ---------------------------
    # FFmpeg filter builder
    # ---------------------------
    def build_video_filter_for_ffmpeg(self):
        """
        Build a -vf filter string from current rotation/flip/crop state.
        """
        parts = []
        
        # Add crop filter if active
        crop_filter = self.player.get_crop_filter()
        if crop_filter:
            parts.append(crop_filter)

        # rotation handling
        r = getattr(self.player, "current_rotation", 0) % 360
        if r == 90:
            parts.append("transpose=1")
        elif r == 270:
            parts.append("transpose=2")
        elif r == 180:
            parts.append("transpose=1,transpose=1")

        # flips
        if getattr(self.player, "flip_horizontal", False):
            parts.append("hflip")
        if getattr(self.player, "flip_vertical", False):
            parts.append("vflip")

        if not parts:
            return None
        
        # برای فرمت WMV، فیلترها را ساده‌تر می‌کنیم
        selected_format = self.get_selected_format()
        if selected_format == "wmv" and len(parts) > 2:
            self.show_info_dialog(
                "WMV Format Notice",
                "WMV format has limited filter support.\n\n"
                "Some complex filters (crop + rotation + flip) may not work properly.\n"
                "Try using simpler filters or choose MP4 format for full feature support."
            )
            # فقط دو فیلتر اول را نگه می‌داریم
            parts = parts[:2]
        
        return ",".join(parts)

    # ---------------------------
    # Progress parsing and runner
    # ---------------------------
    def parse_ffmpeg_progress(self, line, total_duration):
        """
        Try to extract 'time=HH:MM:SS.xx' or 'time=seconds' patterns from ffmpeg stderr and compute progress.
        """
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
                    # single number case
                    current_time = float(m.group(1))
                if total_duration > 0:
                    return min(current_time / total_duration, 1.0)
        return None

    def run_ffmpeg_with_progress(self, cmd, total_duration, output_file):
        """
        Run ffmpeg subprocess and read stderr line-by-line to update progress UI.
        Runs in worker thread.
        """
        try:
            GLib.idle_add(self.status.set_text, f"Processing {os.path.basename(output_file)}...")
            GLib.idle_add(self.progress.set_fraction, 0.0)
            GLib.idle_add(self.percent_label.set_text, "0%")
            GLib.idle_add(self.abort_btn.set_sensitive, True)
            print("FFmpeg command:", " ".join(cmd))

            self.current_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)

            error_lines = []
            # read loop
            while True:
                if not self.is_processing:
                    # user requested abort - no error message needed
                    try:
                        self.current_process.terminate()
                    except Exception:
                        pass
                    return False  # بدون نمایش خطا

                line = self.current_process.stderr.readline()
                if not line and self.current_process.poll() is not None:
                    break

                # جمع‌آوری خطاها برای نمایش بهتر
                if "error" in line.lower() or "failed" in line.lower():
                    error_lines.append(line.strip())

                prog = self.parse_ffmpeg_progress(line, total_duration)
                if prog is not None:
                    GLib.idle_add(self.progress.set_fraction, prog)
                    GLib.idle_add(self.progress.set_text, f"{prog*100:.1f}%")
                    GLib.idle_add(self.percent_label.set_text, f"{prog*100:.1f}%")

                # catch finalizing lines
                if "video:" in (line or "") or "audio:" in (line or ""):
                    GLib.idle_add(self.progress.set_fraction, 1.0)
                    GLib.idle_add(self.progress.set_text, "Finalizing...")
                    GLib.idle_add(self.percent_label.set_text, "100%")

            ret = self.current_process.wait()
            print("ffmpeg return code:", ret)
            
            # اگر خطایی رخ داده، اطلاعات بیشتری نمایش بده
            if ret != 0 and error_lines and self.is_processing:  # فقط اگر کاربر abort نکرده باشه
                error_msg = "\n".join(error_lines[-5:])  # آخرین ۵ خط خطا
                GLib.idle_add(lambda: self.show_error_dialog(
                    "FFmpeg Error", 
                    f"Conversion failed with error:\n\n{error_msg}\n\n"
                    f"Try:\n• Using MP4 format\n• Reducing filter complexity\n• Checking file permissions"
                ))
            
            return ret == 0

        except Exception as e:
            print("Exception in run_ffmpeg_with_progress:", e)
            if self.is_processing:  # فقط اگر کاربر abort نکرده باشه
                GLib.idle_add(lambda: self.show_error_dialog(
                    "Conversion Error",
                    f"An unexpected error occurred:\n\n{str(e)}\n\n"
                    "Please check if FFmpeg is properly installed."
                ))
            return False

    # ---------------------------
    # abort / post actions
    # ---------------------------
    def on_abort(self, widget):
        if self.is_processing and self.current_process:
            self.is_processing = False
            try:
                self.current_process.terminate()
            except Exception:
                pass
            # فقط وضعیت رو آپدیت کن، بدون نمایش پیام خطا
            GLib.idle_add(self.status.set_text, "Processing aborted by user")
            GLib.idle_add(self.abort_btn.set_sensitive, False)
            GLib.idle_add(self.trim_btn.set_sensitive, True)
            # پیشرفت رو هم ریست کن
            GLib.idle_add(self.progress.set_fraction, 0.0)
            GLib.idle_add(self.percent_label.set_text, "0%")

    def execute_post_action(self, action_index, output_file):
        try:
            actions = ["No action", "Close App", "Open Output Folder"]
            action = actions[action_index]
            
            if action == "Close App":
                print("Processing completed. Closing application...")
                GLib.idle_add(Gtk.main_quit)
            elif action == "Open Output Folder":
                output_dir = os.path.dirname(output_file)
                subprocess.Popen(["xdg-open", output_dir])
        except Exception as e:
            print(f"Error executing post action: {e}")
            GLib.idle_add(lambda: self.show_error_dialog(
                "Action Failed", 
                f"Failed to execute action: {str(e)}"
            ))

    # ---------------------------
    # main export/trimming logic
    # ---------------------------
    def on_trim(self, btn):
        path = self.filechooser.get_filename()
        if not path:
            self.show_error_dialog("No Input File", "No input file selected.")
            return
        ok, msg = self.validate_times()
        if not ok:
            self.show_error_dialog("Invalid Time Range", msg)
            return

        # Pause playback for a predictable export state
        if self.player.is_playing:
            self.player.pause()

        start = hmsms_to_seconds(
            self.start_h.get_value_as_int(), 
            self.start_m.get_value_as_int(), 
            self.start_s.get_value_as_int(),
            self.start_ms.get_value_as_int()
        )
        end = hmsms_to_seconds(
            self.end_h.get_value_as_int(), 
            self.end_m.get_value_as_int(), 
            self.end_s.get_value_as_int(),
            self.end_ms.get_value_as_int()
        )
        total_duration = end - start
        
        if total_duration <= 0:
            self.show_error_dialog("Invalid Duration", "Duration must be greater than zero.")
            return
            
        fmt = self.get_selected_format()
        quality = self.settings.get("quality", "1080p")
        bitrate = int(self.settings.get("bitrate", 192))
        base = os.path.splitext(os.path.basename(path))[0]

        def do_trim():
            self.is_processing = True
            GLib.idle_add(self.trim_btn.set_sensitive, False)
            success = False
            out = None
            try:
                quality_suffix = ""
                if quality and quality != "Original" and fmt != "original":
                    if "kbps" in quality:
                        quality_suffix = f"_{quality.split()[0]}kbps"
                    elif "bit" in quality:
                        quality_suffix = f"_{quality.split('-')[0]}"
                    else:
                        quality_suffix = f"_{quality}"

                # compute video filters according to preview state
                vf = self.build_video_filter_for_ffmpeg()
                needs_video_reencode = vf is not None

                # handle "original" case: copy if no transform, otherwise re-encode
                if fmt == "original":
                    ext = os.path.splitext(path)[1]
                    out_name = f"{base}{quality_suffix}"
                    out = unique_output_path(out_name, ext, fmt)
                    if not needs_video_reencode:
                        # simple stream copy (fast)
                        cmd = ["ffmpeg", "-y", "-i", path, "-ss", str(start), "-to", str(end), "-c", "copy", out]
                    else:
                        # must re-encode to apply filters: choose safe defaults
                        cmd = ["ffmpeg", "-y", "-i", path, "-ss", str(start), "-to", str(end),
                               "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                               "-c:a", "aac", "-b:a", f"{bitrate}k", out]
                    success = self.run_ffmpeg_with_progress(cmd, total_duration, out)

                elif fmt in ["mp3", "aac", "wav"]:
                    # Audio formats - ignore crop filters
                    ext = f".{fmt}"
                    out_name = f"{base}{quality_suffix}"
                    out = unique_output_path(out_name, ext, fmt)
                    if fmt == "aac":
                        cmd = ["ffmpeg", "-y", "-i", path, "-ss", str(start), "-to", str(end), "-vn", "-acodec", "aac", "-b:a", f"{bitrate}k", out]
                    elif fmt == "mp3":
                        cmd = ["ffmpeg", "-y", "-i", path, "-ss", str(start), "-to", str(end), "-vn", "-acodec", "libmp3lame", "-b:a", f"{bitrate}k", out]
                    elif fmt == "wav":
                        # WAV: uncompressed PCM 16-bit
                        cmd = ["ffmpeg", "-y", "-i", path, "-ss", str(start), "-to", str(end), "-vn", "-acodec", "pcm_s16le", out]
                    success = self.run_ffmpeg_with_progress(cmd, total_duration, out)

                else:
                    # video re-encoding formats: add -vf if needed
                    ext = f".{fmt}"
                    out_name = f"{base}{quality_suffix}"
                    out = unique_output_path(out_name, ext, fmt)

                    # choose codec set per container - بهبود تنظیمات WMV
                    if fmt == "mp4":
                        codec = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", f"{bitrate}k"]
                    elif fmt == "mkv":
                        codec = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", f"{bitrate}k"]
                    elif fmt == "webm":
                        codec = ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-c:a", "libopus", "-b:a", f"{bitrate}k"]
                    elif fmt == "avi":
                        codec = ["-c:v", "mpeg4", "-qscale:v", "3", "-c:a", "mp3", "-b:a", f"{bitrate}k"]
                    elif fmt == "mov":
                        codec = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", f"{bitrate}k"]
                    elif fmt == "wmv":
                        # تنظیمات بهبود یافته برای WMV
                        codec = [
                            "-c:v", "wmv2", 
                            "-qscale:v", "5",  # کیفیت بهتر
                            "-c:a", "wmav2", 
                            "-b:a", f"{bitrate}k",
                            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"  # اطمینان از ابعاد زوج
                        ]
                        # اگر فیلترهای پیچیده داریم، از کدک ساده‌تر استفاده کنیم
                        if vf and ("transpose" in vf or "hflip" in vf or "vflip" in vf):
                            codec = ["-c:v", "mpeg4", "-qscale:v", "4", "-c:a", "mp3", "-b:a", f"{bitrate}k"]
                    else:
                        codec = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", f"{bitrate}k"]

                    # build command and include vf if necessary
                    if needs_video_reencode and vf:
                        # برای WMV فیلترها را جداگانه اضافه می‌کنیم
                        if fmt == "wmv":
                            cmd = ["ffmpeg", "-y", "-i", path, "-ss", str(start), "-to", str(end), "-vf", vf] + codec + [out]
                        else:
                            cmd = ["ffmpeg", "-y", "-i", path, "-ss", str(start), "-to", str(end), "-vf", vf] + codec + [out]
                    else:
                        cmd = ["ffmpeg", "-y", "-i", path, "-ss", str(start), "-to", str(end)] + codec + [out]

                    success = self.run_ffmpeg_with_progress(cmd, total_duration, out)

                # post-process UI updates and actions
                if success and out:
                    GLib.idle_add(self.status.set_text, f"Saved: {os.path.basename(out)}")
                    GLib.idle_add(self.progress.set_fraction, 1.0)
                    GLib.idle_add(self.percent_label.set_text, "100%")

                    action_index = self.settings.get("action", 0)
                    if action_index != 0:  # اگر "No action" نیست
                        # deferred execution of chosen action (on main thread)
                        GLib.idle_add(self.execute_post_action, action_index, out)
                    else:
                        # NEW: explicitly notify user that processing finished (No action)
                        GLib.idle_add(lambda: self.show_info_dialog("Processing Completed", "Video processing completed successfully!"))
                else:
                    # فقط اگر کاربر abort نکرده باشه خطا رو نشون بده
                    if self.is_processing:
                        GLib.idle_add(lambda: self.show_error_dialog(
                            "Export Failed", 
                            "Failed to export video.\n\n"
                            "Possible reasons:\n"
                            "• Unsupported format combination\n"
                            "• Complex filters with selected format\n"
                            "• Insufficient disk space\n"
                            "• File permission issues"
                        ))
                        GLib.idle_add(self.status.set_text, "Export failed.")

            except Exception as e:
                # فقط اگر کاربر abort نکرده باشه خطا رو نشون بده
                if self.is_processing:
                    GLib.idle_add(lambda: self.show_error_dialog(
                        "Unexpected Error",
                        f"An unexpected error occurred during export:\n\n{str(e)}\n\n"
                        "Please try again with different settings."
                    ))
                    GLib.idle_add(self.status.set_text, "Error occurred.")
            finally:
                # cleanup / reset UI
                self.is_processing = False
                GLib.idle_add(self.abort_btn.set_sensitive, False)
                GLib.idle_add(self.trim_btn.set_sensitive, True)
                self.current_process = None

        # disable button and run worker thread
        self.trim_btn.set_sensitive(False)
        threading.Thread(target=do_trim, daemon=True).start()


if __name__ == "__main__":
    win = NamaCut()
    win.show_all()
    Gtk.main()
