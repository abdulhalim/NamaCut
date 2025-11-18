# player.py
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gst, GLib, Gdk
import os
import subprocess
from .utils import is_video_file, seconds_to_hmsms, hmsms_str

# Custom Seek Bar with Markers
class SeekWithMarkers(Gtk.Scale):
    def __init__(self):
        adjustment = Gtk.Adjustment(0, 0, 1, 0.001, 0.1, 0)
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        
        self.in_position = 0.0
        self.out_position = 1.0
        
        self.set_draw_value(False)

    def set_in_marker(self, position):
        if 0.0 <= position <= 1.0:
            self.in_position = position
            self.queue_draw()

    def set_out_marker(self, position):
        if 0.0 <= position <= 1.0:
            self.out_position = position
            self.queue_draw()

    def do_draw(self, cr):
        Gtk.Scale.do_draw(self, cr)

        allocation = self.get_allocation()
        width = allocation.width
        height = allocation.height

        if width <= 0:
            return

        in_x = int(self.in_position * width)
        out_x = int(self.out_position * width)
        
        if self.in_position > 0.0:
            cr.set_source_rgba(0.2, 0.8, 0.2, 0.8)
            cr.set_line_width(2.0)
            cr.move_to(in_x, 0)
            cr.line_to(in_x, height)
            cr.stroke()
        
        if self.out_position < 1.0:
            cr.set_source_rgba(0.8, 0.2, 0.2, 0.8)
            cr.set_line_width(2.0)
            cr.move_to(out_x, 0)
            cr.line_to(out_x, height)
            cr.stroke()

# Main Embedded Player Widget
class EmbeddedPlayer(Gtk.Box):
    def __init__(self, settings_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Initialize Variables
        self.playbin = Gst.ElementFactory.make("playbin", "player")
        self.duration = None
        self.uri = None
        self.is_seeking = False
        self.is_playing = False
        
        self.current_rotation = 0
        self.flip_horizontal = False
        self.flip_vertical = False
        self.file_type = None
        
        self.in_position = 0.0
        self.out_position = 1.0
        
        self.crop_mode = False
        self.crop_rect = None
        self.crop_handles = []
        self.handle_size = 8
        self.drag_mode = None
        self.drag_start_pos = None
        self.drag_start_rect = None
        
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
        
        self.settings_callback = settings_callback
        self.setup_ui()
        self.setup_gstreamer()
        self.connect_signals()

    # UI Setup
    def setup_ui(self):
        self.video_container = Gtk.Box()
        self.video_container.get_style_context().add_class("video-container")
        
        self.overlay = Gtk.Overlay()
        
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_visible(False)
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | 
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        
        self.invalid_file_label = Gtk.Label()
        self.invalid_file_label.set_visible(False)
        self.invalid_file_label.set_justify(Gtk.Justification.CENTER)
        self.invalid_file_label.set_line_wrap(True)
        
        self.video_container.pack_start(self.overlay, True, True, 0)
        self.overlay.add_overlay(self.drawing_area)
        self.overlay.add_overlay(self.invalid_file_label)
        self.pack_start(self.video_container, True, True, 0)

        self.setup_controls()

    # Playback Controls Setup
    def setup_controls(self):
        controls_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        controls_container.get_style_context().add_class("video-controls")
        self.pack_start(controls_container, False, False, 0)

        all_buttons_row = Gtk.Box(spacing=4)
        
        self.fine_minus_btn = Gtk.Button(label="-0.1s")
        self.fine_minus_btn.set_margin_start(10)
        self.fine_minus_btn.set_size_request(36, 36)
        self.minus_btn = Gtk.Button(label="-1s")
        self.minus_btn.set_size_request(36, 36)
        self.play_pause_btn = Gtk.Button(label="Play")
        self.play_pause_btn.set_size_request(36, 36)
        self.plus_btn = Gtk.Button(label="+1s")
        self.plus_btn.set_size_request(36, 36)
        self.fine_plus_btn = Gtk.Button(label="+0.1s")
        self.fine_plus_btn.set_size_request(36, 36)
        self.in_btn = Gtk.Button(label="Set In")
        self.out_btn = Gtk.Button(label="Set Out")
        
        for btn in [self.fine_minus_btn, self.minus_btn, self.plus_btn, self.fine_plus_btn]:
            btn.set_size_request(36, 36)
            btn.get_style_context().add_class("control-btn")
        self.play_pause_btn.get_style_context().add_class("play-btn")
        self.in_btn.get_style_context().add_class("set-btn")
        self.out_btn.get_style_context().add_class("set-btn")

        all_buttons_row.pack_start(self.fine_minus_btn, False, False, 0)
        all_buttons_row.pack_start(self.minus_btn, False, False, 0)
        all_buttons_row.pack_start(self.play_pause_btn, False, False, 0)
        all_buttons_row.pack_start(self.plus_btn, False, False, 0)
        all_buttons_row.pack_start(self.fine_plus_btn, False, False, 0)
        all_buttons_row.pack_start(self.in_btn, False, False, 0)
        all_buttons_row.pack_start(self.out_btn, False, False, 0)

        self.crop_btn = Gtk.ToggleButton(label="Crop")
        self.crop_btn.get_style_context().add_class("crop-btn")
        all_buttons_row.pack_start(self.crop_btn, False, False, 0)

        self.crop_preset_combo = Gtk.ComboBoxText()
        self.crop_preset_combo.append_text("Free")
        self.crop_preset_combo.append_text("1:1 (Square)")
        self.crop_preset_combo.append_text("16:9 (Widescreen)")
        self.crop_preset_combo.append_text("9:16 (Portrait)")
        self.crop_preset_combo.append_text("4:3 (Standard)")
        self.crop_preset_combo.set_active(0)
        self.crop_preset_combo.get_style_context().add_class("preset-select")
        all_buttons_row.pack_start(self.crop_preset_combo, False, False, 0)
        
        controls_container.pack_start(all_buttons_row, False, False, 0)

        seek_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        seek_container.get_style_context().add_class("seek-container")
        seek_container.set_margin_start(10)
        seek_container.set_margin_end(10)
        seek_container.set_halign(Gtk.Align.FILL)
        
        self.seek = SeekWithMarkers()
        self.seek.get_style_context().add_class("seek-bar")
        self.seek.set_halign(Gtk.Align.FILL)
        
        time_label_center_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        time_label_center_container.set_halign(Gtk.Align.START)
        
        self.time_label = Gtk.Label(label="00:00:00.000/00:00:00.000")
        self.time_label.get_style_context().add_class("time-display")
        self.time_label.set_halign(Gtk.Align.START)
        
        time_label_center_container.pack_start(self.time_label, True, False, 0)
        
        seek_container.pack_start(self.seek, True, True, 0)
        seek_container.pack_start(time_label_center_container, False, False, 0)
        
        controls_container.pack_start(seek_container, False, False, 0)

    # GStreamer Pipeline Setup
    def setup_gstreamer(self):
        if not (self.videoflip and self.videoconvert and self.vsink):
            self.show_fallback_message()
            return
        
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
                self.video_widget.connect("size-allocate", self.on_video_size_allocate)
        except Exception as e:
            print(f"Error getting gtksink widget: {e}")
            self.show_fallback_message()

    # Fallback Message
    def show_fallback_message(self):
        self.invalid_file_label.set_text("Video preview not available. Using external window.")
        self.invalid_file_label.show()

    # Signal Connections
    def connect_signals(self):
        self.play_pause_btn.connect("clicked", self.on_play_pause)
        self.minus_btn.connect("clicked", lambda w: self.seek_delta(-self.get_seek_step()))
        self.plus_btn.connect("clicked", lambda w: self.seek_delta(self.get_seek_step()))
        self.fine_minus_btn.connect("clicked", lambda w: self.seek_delta(-self.get_fine_seek_step()))
        self.fine_plus_btn.connect("clicked", lambda w: self.seek_delta(self.get_fine_seek_step()))
        self.in_btn.connect("clicked", self.on_set_in_clicked)
        self.out_btn.connect("clicked", self.on_set_out_clicked)

        self.seek.connect("button-press-event", self.on_seek_press)
        self.seek.connect("button-release-event", self.on_seek_release)
        self.seek.connect("value-changed", self.on_seek_value_changed)
        
        self.crop_btn.connect("toggled", self.on_crop_mode_toggled)
        self.crop_preset_combo.connect("changed", self.on_crop_preset_changed)
        
        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.connect("button-press-event", self.on_button_press)
        self.drawing_area.connect("button-release-event", self.on_button_release)
        self.drawing_area.connect("motion-notify-event", self.on_motion_notify)

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_bus_message)
        
        GLib.timeout_add(100, self.update_position)

    def on_play_pause(self, widget): 
        self.play() if not self.is_playing else self.pause()
        
    def play(self):
        self.playbin.set_state(Gst.State.PLAYING)
        self.is_playing = True
        self.play_pause_btn.set_label("Pause")
        
    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)
        self.is_playing = False
        self.play_pause_btn.set_label("Play")
        
    def on_video_size_allocate(self, widget, allocation):
        self.display_width = allocation.width
        self.display_height = allocation.height
        self.calculate_padding()

    def on_set_in_clicked(self, widget):
        pos = self.query_position()
        if pos is not None and self.duration:
            self.in_position = pos / self.duration
            self.seek.set_in_marker(self.in_position)
            self.settings_callback()["set_in_callback"]()

    def on_set_out_clicked(self, widget):
        pos = self.query_position()
        if pos is not None and self.duration:
            self.out_position = pos / self.duration
            self.seek.set_out_marker(self.out_position)
            self.settings_callback()["set_out_callback"]()

    def update_markers_from_time_fields(self, start_seconds, end_seconds):
        if self.duration and self.duration > 0:
            self.in_position = start_seconds / self.duration
            self.out_position = end_seconds / self.duration
            self.seek.set_in_marker(self.in_position)
            self.seek.set_out_marker(self.out_position)

    # Crop Interaction Logic
    def on_draw(self, widget, cr):
        if not self.crop_rect or not self.crop_mode:
            return
            
        x, y, w, h = self.crop_rect
        
        cr.set_source_rgba(0, 0, 0, 0.6)
        cr.rectangle(0, 0, self.display_width, y)
        cr.rectangle(0, y, x, h)
        cr.rectangle(x + w, y, self.display_width - x - w, h)
        cr.rectangle(0, y + h, self.display_width, self.display_height - y - h)
        cr.fill()
        
        cr.set_source_rgba(1, 1, 1, 0.8)
        cr.set_line_width(2)
        cr.rectangle(x, y, w, h)
        cr.stroke()
        
        self.draw_handles(cr, x, y, w, h)

    def draw_handles(self, cr, x, y, w, h):
        handles = [
            (x - self.handle_size//2, y - self.handle_size//2),
            (x + w//2 - self.handle_size//2, y - self.handle_size//2),
            (x + w - self.handle_size//2, y - self.handle_size//2),
            (x + w - self.handle_size//2, y + h//2 - self.handle_size//2),
            (x + w - self.handle_size//2, y + h - self.handle_size//2),
            (x + w//2 - self.handle_size//2, y + h - self.handle_size//2),
            (x - self.handle_size//2, y + h - self.handle_size//2),
            (x - self.handle_size//2, y + h//2 - self.handle_size//2),
        ]
        self.crop_handles = handles
        
        cr.set_source_rgba(1, 1, 1, 0.9)
        for hx, hy in handles:
            cr.rectangle(hx, hy, self.handle_size, self.handle_size)
            cr.fill()
            cr.set_source_rgba(0, 0, 0, 0.8)
            cr.set_line_width(1)
            cr.rectangle(hx, hy, self.handle_size, self.handle_size)
            cr.stroke()
            cr.set_source_rgba(1, 1, 1, 0.9)

    def get_hit_type(self, x, y):
        if not self.crop_rect:
            return 'create'
            
        rect_x, rect_y, rect_w, rect_h = self.crop_rect
        
        handle_types = [
            ('resize_tl', rect_x, rect_y),
            ('resize_t', rect_x + rect_w//2, rect_y),
            ('resize_tr', rect_x + rect_w, rect_y),
            ('resize_r', rect_x + rect_w, rect_y + rect_h//2),
            ('resize_br', rect_x + rect_w, rect_y + rect_h),
            ('resize_b', rect_x + rect_w//2, rect_y + rect_h),
            ('resize_bl', rect_x, rect_y + rect_h),
            ('resize_l', rect_x, rect_y + rect_h//2),
        ]
        
        for handle_type, hx, hy in handle_types:
            if (abs(x - hx) <= self.handle_size and abs(y - hy) <= self.handle_size):
                return handle_type
        
        margin = 5
        if (rect_x + margin <= x <= rect_x + rect_w - margin and 
            rect_y + margin <= y <= rect_y + rect_h - margin):
            return 'move'
        
        return 'create'

    def update_cursor(self, x, y):
        hit_type = self.get_hit_type(x, y)
        
        cursor_map = {
            'resize_tl': Gdk.CursorType.TOP_LEFT_CORNER,
            'resize_t': Gdk.CursorType.TOP_SIDE,
            'resize_tr': Gdk.CursorType.TOP_RIGHT_CORNER,
            'resize_r': Gdk.CursorType.RIGHT_SIDE,
            'resize_br': Gdk.CursorType.BOTTOM_RIGHT_CORNER,
            'resize_b': Gdk.CursorType.BOTTOM_SIDE,
            'resize_bl': Gdk.CursorType.BOTTOM_LEFT_CORNER,
            'resize_l': Gdk.CursorType.LEFT_SIDE,
            'move': Gdk.CursorType.FLEUR,
            'create': Gdk.CursorType.CROSSHAIR,
        }
        
        cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), cursor_map.get(hit_type, Gdk.CursorType.ARROW))
        if self.drawing_area.get_window():
            self.drawing_area.get_window().set_cursor(cursor)

    def on_button_press(self, widget, event):
        if self.file_type != "video" or not self.crop_mode:
            return
            
        if event.button == 1:
            x, y = event.x, event.y
            
            x = max(self.padding_x, min(x, self.display_width - self.padding_x))
            y = max(self.padding_y, min(y, self.display_height - self.padding_y))
            
            self.drag_mode = self.get_hit_type(x, y)
            self.drag_start_pos = (x, y)
            
            if self.drag_mode == 'create':
                self.crop_rect = [x, y, 0, 0]
            elif self.drag_mode in ['move', 'resize_tl', 'resize_t', 'resize_tr', 'resize_r', 
                                  'resize_br', 'resize_b', 'resize_bl', 'resize_l']:
                self.drag_start_rect = self.crop_rect.copy()
            
            self.drawing_area.queue_draw()

    def on_motion_notify(self, widget, event):
        if self.file_type != "video" or not self.crop_mode:
            return
            
        x, y = event.x, event.y
        
        x = max(self.padding_x, min(x, self.display_width - self.padding_x))
        y = max(self.padding_y, min(y, self.display_height - self.padding_y))
        
        self.update_cursor(x, y)
        
        if not self.drag_mode or not self.drag_start_pos:
            return
        
        if self.drag_mode == 'create':
            self.crop_rect[2] = x - self.drag_start_pos[0]
            self.crop_rect[3] = y - self.drag_start_pos[1]
            
        elif self.drag_mode == 'move':
            dx = x - self.drag_start_pos[0]
            dy = y - self.drag_start_pos[1]
            new_x = self.drag_start_rect[0] + dx
            new_y = self.drag_start_rect[1] + dy
            
            new_x = max(self.padding_x, min(new_x, self.display_width - self.padding_x - self.drag_start_rect[2]))
            new_y = max(self.padding_y, min(new_y, self.display_height - self.padding_y - self.drag_start_rect[3]))
            
            self.crop_rect[0] = new_x
            self.crop_rect[1] = new_y
            
        elif self.drag_mode.startswith('resize'):
            self.resize_from_handle(self.drag_mode, x, y)
        
        self.drawing_area.queue_draw()

    def on_button_release(self, widget, event):
        if self.file_type != "video" or not self.crop_mode:
            return
            
        if event.button == 1 and self.drag_mode:
            if self.drag_mode == 'create':
                if abs(self.crop_rect[2]) < 10 or abs(self.crop_rect[3]) < 10:
                    self.crop_rect = None
                else:
                    self.crop_rect = self.normalize_rect(self.crop_rect)
                    preset = self.crop_preset_combo.get_active_text()
                    if preset != "Free":
                        self.apply_aspect_ratio_on_creation()
            
            self.drag_mode = None
            self.drag_start_pos = None
            self.drag_start_rect = None
            self.drawing_area.queue_draw()

    def normalize_rect(self, rect):
        if not rect: return None
        x, y, w, h = rect
        if w < 0:
            x += w
            w = -w
        if h < 0:
            y += h
            h = -h
        return [x, y, w, h]

    def apply_aspect_ratio_on_creation(self):
        if not self.crop_rect: return
        preset = self.crop_preset_combo.get_active_text()
        if preset == "Free": return

        target_ratio = {
            "1:1 (Square)": 1.0,
            "16:9 (Widescreen)": 16.0/9.0,
            "9:16 (Portrait)": 9.0/16.0,
            "4:3 (Standard)": 4.0/3.0,
        }.get(preset)

        if not target_ratio: return
        x, y, w, h = self.crop_rect
        current_ratio = w / h

        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            self.crop_rect[0] += (w - new_w) // 2
            self.crop_rect[2] = new_w
        else:
            new_h = int(w / target_ratio)
            self.crop_rect[1] += (h - new_h) // 2
            self.crop_rect[3] = new_h

    def resize_from_handle(self, handle, x, y):
        preset = self.crop_preset_combo.get_active_text()
        
        if preset == "Free":
            x1, y1, w1, h1 = self.drag_start_rect
            
            if handle == 'resize_br': 
                self.crop_rect = [x1, y1, x - x1, y - y1]
            elif handle == 'resize_tl': 
                self.crop_rect = [x, y, (x1 + w1) - x, (y1 + h1) - y]
            elif handle == 'resize_tr': 
                self.crop_rect = [x1, y, x - x1, (y1 + h1) - y]
            elif handle == 'resize_bl': 
                self.crop_rect = [x, y1, (x1 + w1) - x, y - y1]
            elif handle == 'resize_r': 
                self.crop_rect = [x1, y1, x - x1, h1]
            elif handle == 'resize_l': 
                self.crop_rect = [x, y1, (x1 + w1) - x, h1]
            elif handle == 'resize_b': 
                self.crop_rect = [x1, y1, w1, y - y1]
            elif handle == 'resize_t': 
                self.crop_rect = [x1, y, w1, (y1 + h1) - y]
            
            self.crop_rect = self.normalize_rect(self.crop_rect)
            return

        target_ratio = {
            "1:1 (Square)": 1.0,
            "16:9 (Widescreen)": 16.0/9.0,
            "9:16 (Portrait)": 9.0/16.0,
            "4:3 (Standard)": 4.0/3.0,
        }.get(preset)
        
        if not target_ratio:
            return

        x1, y1, w1, h1 = self.drag_start_rect
        min_x, max_x = self.padding_x, self.display_width - self.padding_x
        min_y, max_y = self.padding_y, self.display_height - self.padding_y

        new_rect = None
        
        if handle == 'resize_r':
            new_width = max(10, x - x1)
            new_height = int(new_width / target_ratio)
            new_rect = [x1, y1, new_width, new_height]
            
        elif handle == 'resize_l':
            new_width = max(10, (x1 + w1) - x)
            new_height = int(new_width / target_ratio)
            new_x = x
            new_rect = [new_x, y1, new_width, new_height]
            
        elif handle == 'resize_b':
            new_height = max(10, y - y1)
            new_width = int(new_height * target_ratio)
            new_rect = [x1, y1, new_width, new_height]
            
        elif handle == 'resize_t':
            new_height = max(10, (y1 + h1) - y)
            new_width = int(new_height * target_ratio)
            new_y = y
            new_rect = [x1, new_y, new_width, new_height]
            
        elif handle == 'resize_br':
            new_width = max(10, x - x1)
            new_height = int(new_width / target_ratio)
            new_rect = [x1, y1, new_width, new_height]
            
        elif handle == 'resize_tr':
            new_width = max(10, x - x1)
            new_height = int(new_width / target_ratio)
            new_y = y1 + h1 - new_height
            new_rect = [x1, new_y, new_width, new_height]
            
        elif handle == 'resize_bl':
            new_width = max(10, (x1 + w1) - x)
            new_height = int(new_width / target_ratio)
            new_x = x
            new_rect = [new_x, y1, new_width, new_height]
            
        elif handle == 'resize_tl':
            new_width = max(10, (x1 + w1) - x)
            new_height = int(new_width / target_ratio)
            new_x = x
            new_y = y1 + h1 - new_height
            new_rect = [new_x, new_y, new_width, new_height]

        if new_rect:
            new_x, new_y, new_w, new_h = new_rect
            
            if new_x < min_x:
                new_x = min_x
            if new_x + new_w > max_x:
                new_w = max_x - new_x
                
            if new_y < min_y:
                new_y = min_y
            if new_y + new_h > max_y:
                new_h = max_y - new_y
                
            current_ratio = new_w / new_h
            if abs(current_ratio - target_ratio) > 0.01:
                if current_ratio > target_ratio:
                    new_h = int(new_w / target_ratio)
                else:
                    new_w = int(new_h * target_ratio)
                
                if new_x + new_w > max_x:
                    new_w = max_x - new_x
                    new_h = int(new_w / target_ratio)
                if new_y + new_h > max_y:
                    new_h = max_y - new_y
                    new_w = int(new_h * target_ratio)
            
            new_w = max(10, new_w)
            new_h = max(10, new_h)
            
            self.crop_rect = [new_x, new_y, new_w, new_h]
            self.crop_rect = self.normalize_rect(self.crop_rect)

    def on_crop_mode_toggled(self, widget):
        if self.file_type != "video":
            widget.set_active(False)
            return
            
        self.crop_mode = widget.get_active()
        self.drawing_area.set_visible(self.crop_mode)
        
        if self.crop_mode and not self.crop_rect:
            self.create_default_crop_rect()
        elif not self.crop_mode:
            self.crop_rect = None
            self.crop_handles = []
            self.drawing_area.queue_draw()
            if self.drawing_area.get_window():
                self.drawing_area.get_window().set_cursor(None)

    def on_crop_preset_changed(self, widget):
        if not self.crop_mode:
            return
        
        self.crop_rect = None
        self.crop_handles = []
        
        self.create_default_crop_rect()
        
        self.drawing_area.queue_draw()

    def create_default_crop_rect(self):
        if not self.display_width or not self.display_height:
            return
            
        usable_w = self.display_width - 2 * self.padding_x
        usable_h = self.display_height - 2 * self.padding_y
        
        if usable_w <= 0 or usable_h <= 0:
            return
        
        center_x = self.display_width // 2
        center_y = self.display_height // 2
        
        preset = self.crop_preset_combo.get_active_text()
        
        if preset == "Free":
            w, h = usable_w // 2, usable_h // 2
        else:
            target_ratio = {
                "1:1 (Square)": 1.0,
                "16:9 (Widescreen)": 16.0/9.0,
                "9:16 (Portrait)": 9.0/16.0,
                "4:3 (Standard)": 4.0/3.0,
            }.get(preset, 1.0)
            
            if target_ratio >= 1.0:
                max_width = min(usable_w, int(usable_h * target_ratio))
                w = max_width * 2 // 3
                h = int(w / target_ratio)
            else:
                max_height = min(usable_h, int(usable_w / target_ratio))
                h = max_height * 2 // 3
                w = int(h * target_ratio)
        
        w = max(50, w)
        h = max(50, h)
        
        x = max(self.padding_x, min(center_x - w//2, self.display_width - self.padding_x - w))
        y = max(self.padding_y, min(center_y - h//2, self.display_height - self.padding_y - h))
        
        self.crop_rect = [x, y, w, h]
        self.drawing_area.queue_draw()

    # File and Video Management
    def set_file(self, path):
        if not path: return
        
        self.playbin.set_state(Gst.State.NULL)
        
        if not is_video_file(path):
            self.show_invalid_file_message()
            return
        
        self.file_type = "video"
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
        
        self.in_position = 0.0
        self.out_position = 1.0
        self.seek.set_in_marker(self.in_position)
        self.seek.set_out_marker(self.out_position)
        
        self.setup_video_mode(path)
        self.playbin.set_state(Gst.State.PAUSED)

    def show_invalid_file_message(self):
        if self.use_gtksink: self.video_widget.hide()
        self.invalid_file_label.set_text("Invalid video file!\n\nPlease select a valid video file.")
        self.invalid_file_label.show()
        self.drawing_area.set_visible(False)
        self.time_label.set_text("00:00:00.000/00:00:00.000")
        self.seek.set_range(0.0, 1.0)
        self.seek.set_value(0.0)

    def setup_video_mode(self, path):
        self.get_video_size()
        if self.use_gtksink: self.video_widget.show()
        self.invalid_file_label.hide()
        self.drawing_area.set_visible(False)
        if getattr(self, "videoflip", None):
            try: self.videoflip.set_property("method", 0)
            except Exception: pass
        self.time_label.set_text("00:00:00.000/00:00:00.000")
        self.seek.set_range(0.0, 1.0)
        self.seek.set_value(0.0)

    def get_video_size(self):
        if not self.uri: return None, None
        try:
            result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", self.uri], capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split(','))
            self.video_width = width
            self.video_height = height
            GLib.idle_add(self.calculate_padding)
            return width, height
        except Exception as e:
            print(f"Error getting video size: {e}")
            return None, None

    def get_effective_video_dimensions(self):
        w, h = self.video_width, self.video_height
        
        if self.current_rotation % 180 == 90:
            w, h = h, w
            
        return w, h

    def calculate_padding(self):
        if not all([self.video_width, self.video_height, self.display_width, self.display_height]): return
        
        effective_w, effective_h = self.get_effective_video_dimensions()
        
        video_ratio = effective_w / effective_h
        display_ratio = self.display_width / self.display_height
        
        if video_ratio > display_ratio:
            scaled_height = int(self.display_width / video_ratio)
            self.padding_y = (self.display_height - scaled_height) // 2
            self.padding_x = 0
        else:
            scaled_width = int(self.display_height * video_ratio)
            self.padding_x = (self.display_width - scaled_width) // 2
            self.padding_y = 0
        
        if self.crop_mode and self.crop_rect:
            self.drawing_area.queue_draw()

    # Seeking and Playback Logic
    def seek_to(self, seconds):
        if seconds < 0: seconds = 0
        if self.duration: seconds = min(seconds, self.duration)
        try: self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE, int(seconds * Gst.SECOND))
        except Exception as e: print(f"Seek error: {e}")
        
    def seek_delta(self, delta):
        pos = self.query_position()
        if pos is not None: self.seek_to(pos + delta)

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
            if self.duration is None: self.query_duration()
            if self.duration: self.seek.set_range(0.0, self.duration)
            if pos is not None:
                self.seek.set_value(pos)
                if self.duration: self.time_label.set_text(f"{hmsms_str(pos)}/{hmsms_str(self.duration)}")
                else: self.time_label.set_text(f"{hmsms_str(pos)}/00:00:00.000")
        return True

    def on_seek_press(self, widget, event): self.is_seeking = True
    def on_seek_release(self, widget, event):
        self.is_seeking = False
        self.seek_to(self.seek.get_value())
    def on_seek_value_changed(self, widget):
        if self.is_seeking:
            val = self.seek.get_value()
            self.time_label.set_text(f"{hmsms_str(val)}/00:00:00.000")

    def on_bus_message(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.EOS:
            self.playbin.set_state(Gst.State.PAUSED)
            self.is_playing = False
            self.play_pause_btn.set_label("Play")
            self.seek_to(0)
        elif t == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            print("GStreamer error:", err, dbg)
            self.playbin.set_state(Gst.State.NULL)
            self.is_playing = False
            self.play_pause_btn.set_label("Play")
        elif t == Gst.MessageType.STATE_CHANGED:
            if msg.src == self.playbin:
                old_state, new_state, pending_state = msg.parse_state_changed()
                if new_state == Gst.State.PAUSED and old_state == Gst.State.READY:
                    self.get_video_size()

    # Video Transformation
    def rotate_video(self, rotation_type):
        if not self.uri or self.file_type != "video": return
        if rotation_type == "left": self.current_rotation = (self.current_rotation - 90) % 360
        elif rotation_type == "right": self.current_rotation = (self.current_rotation + 90) % 360
        elif rotation_type == "horizontal": self.flip_horizontal = not self.flip_horizontal
        elif rotation_type == "vertical": self.flip_vertical = not self.flip_vertical
        elif rotation_type == "reset":
            self.current_rotation = 0
            self.flip_horizontal = False
            self.flip_vertical = False
            self.clear_crop()
        
        if self.crop_mode:
            self.crop_btn.set_active(False)
        
        self.apply_video_filters()
        
        GLib.idle_add(self.calculate_padding)
        
        if not self.is_playing:
            pos = self.query_position()
            if pos is not None: self.seek_to(pos)

    def apply_video_filters(self):
        if not getattr(self, "videoflip", None) or self.file_type != "video": return
        method = self._compute_videoflip_method()
        try: self.videoflip.set_property("method", method)
        except Exception as e: print(f"Error setting videoflip method: {e}")

    def _compute_videoflip_method(self):
        rot_map = {0:0, 90:1, 180:2, 270:3}
        r = self.current_rotation % 360
        if r not in rot_map: r = 0
        if not self.flip_horizontal and not self.flip_vertical: return rot_map[r]
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

    # Utility and Filter Methods
    def clear_crop(self):
        self.crop_rect = None
        self.crop_handles = []
        if self.crop_mode: self.drawing_area.queue_draw()

    def get_seek_step(self):
        settings = self.settings_callback()
        return settings.get("seek_step", 1.0)
    def get_fine_seek_step(self):
        settings = self.settings_callback()
        return settings.get("fine_seek_step", 0.1)

    def get_crop_filter(self):
        if not self.crop_rect or not self.crop_mode or self.file_type != "video":
            return None
        
        if not self.video_width or not self.video_height:
            return None
        
        x, y, w, h = self.crop_rect
        
        effective_w, effective_h = self.get_effective_video_dimensions()
        video_display_w = self.display_width - 2 * self.padding_x
        video_display_h = self.display_height - 2 * self.padding_y
        
        if video_display_w <= 0 or video_display_h <= 0: return None

        scale_x = effective_w / video_display_w
        scale_y = effective_h / video_display_h
        
        effective_video_x = int((x - self.padding_x) * scale_x)
        effective_video_y = int((y - self.padding_y) * scale_y)
        effective_video_w = int(w * scale_x)
        effective_video_h = int(h * scale_y)
        
        orig_video_x, orig_video_y, orig_video_w, orig_video_h = 0, 0, 0, 0
        
        r = self.current_rotation % 360
        if r == 0:
            orig_video_x, orig_video_y, orig_video_w, orig_video_h = effective_video_x, effective_video_y, effective_video_w, effective_video_h
        elif r == 90:
            orig_video_x = effective_video_y
            orig_video_y = self.video_height - effective_video_x - effective_video_w
            orig_video_w = effective_video_h
            orig_video_h = effective_video_w
        elif r == 180:
            orig_video_x = self.video_width - effective_video_x - effective_video_w
            orig_video_y = self.video_height - effective_video_y - effective_video_h
            orig_video_w = effective_video_w
            orig_video_h = effective_video_h
        elif r == 270:
            orig_video_x = self.video_width - effective_video_y - effective_video_h
            orig_video_y = effective_video_x
            orig_video_w = effective_video_h
            orig_video_h = effective_video_w

        if self.flip_horizontal:
            orig_video_x = self.video_width - orig_video_x - orig_video_w
        if self.flip_vertical:
            orig_video_y = self.video_height - orig_video_y - orig_video_h
        
        orig_video_w = orig_video_w & ~1
        orig_video_h = orig_video_h & ~1
        
        orig_video_x = max(0, min(orig_video_x, self.video_width - 2))
        orig_video_y = max(0, min(orig_video_y, self.video_height - 2))
        orig_video_w = min(orig_video_w, self.video_width - orig_video_x)
        orig_video_h = min(orig_video_h, self.video_height - orig_video_y)
        
        if orig_video_w <= 0 or orig_video_h <= 0: return None
        
        return f"crop={orig_video_w}:{orig_video_h}:{orig_video_x}:{orig_video_y}"

    def build_video_filter_for_ffmpeg(self):
        parts = []
        
        crop_filter = self.get_crop_filter()
        if crop_filter: parts.append(crop_filter)

        r = getattr(self, "current_rotation", 0) % 360
        if r == 90: parts.append("transpose=1")
        elif r == 270: parts.append("transpose=2")
        elif r == 180: parts.append("transpose=1,transpose=1")

        if getattr(self, "flip_horizontal", False): parts.append("hflip")
        if getattr(self, "flip_vertical", False): parts.append("vflip")

        if not parts: return None
        return ",".join(parts)
