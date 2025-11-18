#!/usr/bin/env python3
# Main application entry point
import gi
import os
import sys
import subprocess

# Add modules directory to Python path for development
# This line is harmless after installation as the package is already in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
if os.path.isdir(modules_dir) and modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gst, GLib, Gdk
from modules.player import EmbeddedPlayer
from modules.settings import SettingsManager
from modules.export import ExportManager
from modules.utils import is_video_file, seconds_to_hmsms, hmsms_str, hmsms_to_seconds

Gst.init(None)

# Main application window
class NamaCut(Gtk.Window):
    def __init__(self):
        super().__init__(title="NamaCut v2.0")
        self.set_default_size(1000, 700)
        self.set_size_request(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", self.on_window_destroy)
        
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        
        self.export_manager = ExportManager(self)
        
        self.setup_drag_drop()
        self.apply_css()
        self.setup_ui()
        
        self.current_process = None
        self.is_processing = False
        self.current_output_file = None
        
        self.show_all()

    # Setup drag and drop
    def setup_drag_drop(self):
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.connect("drag-data-received", self.on_drag_data_received)

    # Apply CSS styles
    def apply_css(self):
        css_provider = Gtk.CssProvider()
        
        # Robustly find the CSS file, both in development and after installation
        try:
            # Try to find the 'modules' package from the Python path (installed case)
            import modules
            base_path = os.path.dirname(modules.__file__)
            css_path = os.path.join(base_path, 'styles', 'style.css')
        except ImportError:
            # Fallback for development, assuming 'modules' is next to this script
            base_path = os.path.dirname(os.path.abspath(__file__))
            css_path = os.path.join(base_path, 'modules', 'styles', 'style.css')
        
        try:
            if os.path.exists(css_path):
                css_provider.load_from_path(css_path)
            else:
                # If file is not found, use fallback CSS
                css_provider.load_from_data(self.get_fallback_css().encode('utf-8'))
        except Exception as e:
            print(f"Error loading CSS: {e}")
            css_provider.load_from_data(self.get_fallback_css().encode('utf-8'))
        
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # Fallback CSS if no file is found
    def get_fallback_css(self):
        return """
        * { font-family: "Cantarell", "Sans", "Arial"; }
        .main-container { background-color: #1e1e2e; color: #cdd6f4; }
        dialog { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog > box { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog .content-area { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog .action-area { background-color: #1e1e2e; border-top: 1px solid #313244; }
        .dialog notebook { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog notebook > stack > box { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog headerbar { background-color: #1e1e2e; color: #cdd6f4; border-bottom: 1px solid #313244; }
        .dialog headerbar .title { color: #cdd6f4; }
        .dialog button { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 6px 12px; min-height: 24px; }
        .dialog button:hover { background-color: #45475a; }
        .dialog button:active { background-color: #585b70; }
        .dialog combobox { background-color: #313244; color: #cdd6f4; }
        .dialog combobox box { background-color: #313244; color: #cdd6f4; }
        .dialog combobox button { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; }
        .dialog entry { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px 8px; }
        .dialog scale { background-color: #313244; color: #cdd6f4; }
        .dialog scale trough { background-color: #45475a; border-radius: 4px; min-height: 6px; }
        .dialog scale trough highlight { background-color: #89b4fa; border-radius: 4px; min-height: 6px; }
        .dialog scale trough slider { background-color: #89b4fa; border: 2px solid #cdd6f4; border-radius: 50%; min-width: 12px; min-height: 12px; margin: -6px; }
        .dialog label { color: #cdd6f4; }
        .dialog frame { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 8px; }
        .dialog frame > border { border: 1px solid #313244; border-radius: 8px; }
        .dialog frame > label { color: #cdd6f4; background-color: #1e1e2e; }
        .message-dialog { background-color: #1e1e2e; color: #cdd6f4; }
        .message-dialog .titlebar { background-color: #1e1e2e; color: #cdd6f4; }
        .message-dialog .dialog-action-area { background-color: #1e1e2e; border-top: 1px solid #313244; }
        .message-dialog .dialog-action-area button { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; }
        .message-dialog .dialog-action-area button:hover { background-color: #45475a; }
        .file-row { background-color: #181825; border-radius: 6px; padding: 8px; margin-bottom: 4px; }
        .panel { background: rgba(24, 24, 37, 0.95); border: 1px solid #313244; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
        .edit-btn { background-color: #313244; border: none; color: #cdd6f4; padding: 6px; border-radius: 4px; font-size: 11px; }
        .edit-btn:hover { background-color: #45475a; }
        .export-btn { background-color: #89b4fa; color: #1e1e2e; border: none; border-radius: 4px; font-weight: 600; padding: 6px; font-size: 11px; }
        .export-btn:hover { background-color: #74c7ec; }
        .abort-btn { background-color: #f38ba8; color: #1e1e2e; border: none; border-radius: 4px; font-weight: 600; padding: 6px; font-size: 11px; }
        .abort-btn:hover { background-color: #eba0ac; }
        .quit-btn { background-color: #313244; border: none; color: #cdd6f4; padding: 6px; border-radius: 4px; font-size: 11px; }
        .quit-btn:hover { background-color: #45475a; }
        .seek-bar { background-color: #313244; color: #cdd6f4; }
        .seek-bar trough { background-color: #45475a; border-radius: 4px; min-height: 6px; }
        .seek-bar trough highlight { background-color: #89b4fa; border-radius: 4px; min-height: 6px; }
        .seek-bar trough slider { background-color: #89b4fa; border: 2px solid #cdd6f4; border-radius: 50%; min-width: 12px; min-height: 12px; margin: -6px; }
        .time-display { color: #cdd6f4; font-family: monospace; font-size: 11px; }
        .time-section-label { color: #cdd6f4; font-weight: 600; font-size: 13px; margin-bottom: 4px; }
        separator { background-color: #45475a; min-width: 1px; }
        .video-info-label { color: #cdd6f4; font-family: monospace; font-size: 11px; margin-left: 8px; }
        .file-chooser { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; }
        .about-btn { background-color: #313244; border: 1px solid #45475a; color: #cdd6f4; border-radius: 4px; padding: 6px; }
        .about-btn:hover { background-color: #45475a; }
        """

    # Setup main UI
    def setup_ui(self):
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        main_container.set_border_width(6)
        main_container.get_style_context().add_class("main-container")
        self.add(main_container)

        self.setup_file_row(main_container)
        
        main_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_content.get_style_context().add_class("main-content")
        main_container.pack_start(main_content, True, True, 0)

        self.setup_left_panel(main_content)
        self.setup_right_panel(main_content)
        
        self.setup_time_controls(main_container)
        self.setup_progress_bar(main_container)

    # Setup top file row
    def setup_file_row(self, parent):
        file_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        file_row.get_style_context().add_class("file-row")
        
        self.filechooser = Gtk.FileChooserButton(title="Select video file", action=Gtk.FileChooserAction.OPEN)
        self.filechooser.set_filter(self.file_filter())
        self.filechooser.get_style_context().add_class("file-chooser")
        self.filechooser.set_size_request(300, -1)
        file_row.pack_start(self.filechooser, False, False, 0)
        
        self.video_info_label = Gtk.Label(label="No video loaded")
        self.video_info_label.get_style_context().add_class("video-info-label")
        self.video_info_label.set_line_wrap(True)
        self.video_info_label.set_max_width_chars(40)
        file_row.pack_start(self.video_info_label, True, True, 0)
        
        self.about_btn = Gtk.Button()
        self.about_btn.set_tooltip_text("About")
        about_icon = Gtk.Image.new_from_icon_name("help-about-symbolic", Gtk.IconSize.BUTTON)
        self.about_btn.set_image(about_icon)
        self.about_btn.get_style_context().add_class("about-btn")
        self.about_btn.connect("clicked", self.on_about_clicked)
        file_row.pack_start(self.about_btn, False, False, 0)
        
        parent.pack_start(file_row, False, False, 0)
        
        self.filechooser.connect("file-set", self.on_file_selected)

    # Setup left panel (video player)
    def setup_left_panel(self, parent):
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        left_panel.get_style_context().add_class("left-panel")
        
        video_frame = Gtk.Frame()
        video_frame.set_shadow_type(Gtk.ShadowType.NONE)
        video_frame.get_style_context().add_class("video-frame")
        
        self.player = EmbeddedPlayer(self.get_settings)
        video_frame.add(self.player)
        left_panel.pack_start(video_frame, True, True, 0)
        
        parent.pack_start(left_panel, True, True, 0)

    # Setup right panel (controls)
    def setup_right_panel(self, parent):
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right_panel.set_size_request(300, -1)
        right_panel.get_style_context().add_class("right-panel")
        
        self.setup_edit_video_section(right_panel)
        self.setup_output_section(right_panel)
        self.setup_after_export_section(right_panel)
        self.setup_action_buttons(right_panel)
        
        parent.pack_start(right_panel, False, False, 0)

    # Setup edit video section
    def setup_edit_video_section(self, parent):
        edit_frame = Gtk.Frame(label="Rotation & Flip")
        edit_frame.get_style_context().add_class("panel")
        edit_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        edit_frame.add(edit_box)
        parent.pack_start(edit_frame, False, False, 0)

        video_controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        video_controls_box.get_style_context().add_class("edit-controls")
        
        first_row = Gtk.Box(spacing=3)
        self.rotate_left_btn = Gtk.Button(label="↶ 90°")
        self.rotate_right_btn = Gtk.Button(label="90° ↷")
        self.rotate_left_btn.get_style_context().add_class("edit-btn")
        self.rotate_right_btn.get_style_context().add_class("edit-btn")
        first_row.pack_start(self.rotate_left_btn, True, True, 0)
        first_row.pack_start(self.rotate_right_btn, True, True, 0)
        video_controls_box.pack_start(first_row, False, False, 0)
        
        second_row = Gtk.Box(spacing=3)
        self.flip_horizontal_btn = Gtk.Button(label="↔ Flip H")
        self.flip_vertical_btn = Gtk.Button(label="↕ Flip V")
        self.flip_horizontal_btn.get_style_context().add_class("edit-btn")
        self.flip_vertical_btn.get_style_context().add_class("edit-btn")
        second_row.pack_start(self.flip_horizontal_btn, True, True, 0)
        second_row.pack_start(self.flip_vertical_btn, True, True, 0)
        video_controls_box.pack_start(second_row, False, False, 0)
        
        third_row = Gtk.Box(spacing=3)
        self.reset_rotation_btn = Gtk.Button(label="⟲ Reset")
        self.reset_rotation_btn.get_style_context().add_class("edit-btn")
        third_row.pack_start(self.reset_rotation_btn, True, True, 0)
        video_controls_box.pack_start(third_row, False, False, 0)
        
        edit_box.pack_start(video_controls_box, False, False, 0)

        self.connect_video_controls()

    # Connect video control signals
    def connect_video_controls(self):
        self.rotate_left_btn.connect("clicked", lambda w: self.player.rotate_video("left"))
        self.rotate_right_btn.connect("clicked", lambda w: self.player.rotate_video("right"))
        self.flip_horizontal_btn.connect("clicked", lambda w: self.player.rotate_video("horizontal"))
        self.flip_vertical_btn.connect("clicked", lambda w: self.player.rotate_video("vertical"))
        self.reset_rotation_btn.connect("clicked", lambda w: self.player.rotate_video("reset"))

    # Setup output section
    def setup_output_section(self, parent):
        output_frame = Gtk.Frame(label="Output")
        output_frame.get_style_context().add_class("panel")
        output_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        output_frame.add(output_box)
        parent.pack_start(output_frame, False, False, 0)

        self.format_combo = Gtk.ComboBoxText()
        for label, tag in [
            ("Original - Copy", "original"), ("MP4", "mp4"), ("MKV", "mkv"), ("WEBM", "webm"), 
            ("AVI", "avi"), ("MOV", "mov"), ("WMV", "wmv"), ("FLV", "flv"), ("MPEG", "mpeg"), ("TS", "ts")
        ]:
            self.format_combo.append_text(label)
        
        format_index = self.settings.get("format_index", 0)
        item_count = self.get_combo_item_count(self.format_combo)
        if format_index < item_count:
            self.format_combo.set_active(format_index)
        else:
            self.format_combo.set_active(0)
            
        self.format_combo.set_no_show_all(True)
        self.format_combo.hide()
        output_box.pack_start(self.format_combo, False, False, 0)

        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        format_box.get_style_context().add_class("output-format")
        format_label = Gtk.Label(label="Format:")
        format_label.get_style_context().add_class("format-label")
        self.format_value_label = Gtk.Label(label=self.get_format_display_text())
        self.format_value_label.get_style_context().add_class("format-value")
                
        settings_icon = Gtk.Image.new_from_icon_name("preferences-system", Gtk.IconSize.BUTTON)

        settings_btn = Gtk.Button()
        settings_btn.set_image(settings_icon)
        settings_btn.set_always_show_image(True) 
        settings_btn.set_tooltip_text("Output Settings")
        settings_btn.get_style_context().add_class("settings-btn")
        
        format_box.pack_start(format_label, False, False, 0)
        format_box.pack_start(self.format_value_label, True, True, 0)
        format_box.pack_start(settings_btn, False, False, 0)
        output_box.pack_start(format_box, False, False, 0)
        
        settings_btn.connect("clicked", self.on_settings_clicked)
        self.format_combo.connect("changed", self.on_format_changed)

    # Setup after export section
    def setup_after_export_section(self, parent):
        action_frame = Gtk.Frame(label="After Export")
        action_frame.get_style_context().add_class("panel")
        action_frame.set_margin_top(8)
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        action_frame.add(action_box)
        parent.pack_start(action_frame, False, False, 0)

        control_label = Gtk.Label(label="Choose an action:")
        control_label.get_style_context().add_class("control-label")
        control_label.set_halign(Gtk.Align.START)
        action_box.pack_start(control_label, False, False, 0)

        self.action_combo = Gtk.ComboBoxText()
        for t in ("Show completion message", "Open Output Folder", "Close Application"):
            self.action_combo.append_text(t)
        self.action_combo.set_active(self.settings.get("action", 0))
        self.action_combo.get_style_context().add_class("post-action-select")
        self.action_combo.set_halign(Gtk.Align.START)
        action_box.pack_start(self.action_combo, False, False, 0)

    # Setup action buttons
    def setup_action_buttons(self, parent):
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        buttons_box.get_style_context().add_class("action-buttons")
        buttons_box.set_margin_top(8)
        
        self.export_btn = Gtk.Button(label="Export")
        self.export_btn.get_style_context().add_class("export-btn")
        self.abort_btn = Gtk.Button(label="Abort")
        self.abort_btn.get_style_context().add_class("abort-btn")
        self.abort_btn.set_sensitive(False)
        self.quit_btn = Gtk.Button(label="Quit")
        self.quit_btn.get_style_context().add_class("quit-btn")

        buttons_box.pack_start(self.export_btn, True, True, 0)
        buttons_box.pack_start(self.abort_btn, True, True, 0)
        buttons_box.pack_start(self.quit_btn, True, True, 0)
        parent.pack_start(buttons_box, False, False, 0)

        self.export_btn.connect("clicked", self.on_export)
        self.abort_btn.connect("clicked", self.on_abort)
        self.quit_btn.connect("clicked", self.on_quit_clicked)

    # Setup time controls
    def setup_time_controls(self, parent):
        time_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        time_box.get_style_context().add_class("time-box")
        
        main_time_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_time_container.set_halign(Gtk.Align.START)
        main_time_container.set_margin_start(10)
        
        start_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        start_container.set_halign(Gtk.Align.START)
        
        start_label = Gtk.Label(label="Start")
        start_label.get_style_context().add_class("time-section-label")
        
        start_box = Gtk.Box(spacing=2)
        start_box.get_style_context().add_class("time-inputs")
        
        self.start_h = Gtk.SpinButton.new_with_range(0, 99, 1)
        self.start_h.set_size_request(45, -1)
        self.start_m = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.start_m.set_size_request(45, -1)
        self.start_s = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.start_s.set_size_request(45, -1)
        self.start_ms = Gtk.SpinButton.new_with_range(0, 999, 1)
        self.start_ms.set_size_request(45, -1)
        
        start_box.pack_start(self.start_h, False, False, 0)
        start_box.pack_start(Gtk.Label(label="h"), False, False, 0)
        start_box.pack_start(self.start_m, False, False, 0)
        start_box.pack_start(Gtk.Label(label="m"), False, False, 0)
        start_box.pack_start(self.start_s, False, False, 0)
        start_box.pack_start(Gtk.Label(label="s"), False, False, 0)
        start_box.pack_start(self.start_ms, False, False, 0)
        start_box.pack_start(Gtk.Label(label="ms"), False, False, 0)
        
        start_container.pack_start(start_label, False, False, 0)
        start_container.pack_start(start_box, False, False, 0)
        
        end_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        end_container.set_halign(Gtk.Align.START)
        
        end_label = Gtk.Label(label="End")
        end_label.get_style_context().add_class("time-section-label")
        
        end_box = Gtk.Box(spacing=2)
        end_box.get_style_context().add_class("time-inputs")
        
        self.end_h = Gtk.SpinButton.new_with_range(0, 99, 1)
        self.end_h.set_size_request(45, -1)
        self.end_m = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.end_m.set_size_request(45, -1)
        self.end_s = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.end_s.set_size_request(45, -1)
        self.end_ms = Gtk.SpinButton.new_with_range(0, 999, 1)
        self.end_ms.set_size_request(45, -1)
        
        end_box.pack_start(self.end_h, False, False, 0)
        end_box.pack_start(Gtk.Label(label="h"), False, False, 0)
        end_box.pack_start(self.end_m, False, False, 0)
        end_box.pack_start(Gtk.Label(label="m"), False, False, 0)
        end_box.pack_start(self.end_s, False, False, 0)
        end_box.pack_start(Gtk.Label(label="s"), False, False, 0)
        end_box.pack_start(self.end_ms, False, False, 0)
        end_box.pack_start(Gtk.Label(label="ms"), False, False, 0)
        
        end_container.pack_start(end_label, False, False, 0)
        end_container.pack_start(end_box, False, False, 0)
        
        main_time_container.pack_start(start_container, False, False, 0)
        main_time_container.pack_start(end_container, False, False, 0)
        
        time_box.pack_start(main_time_container, True, False, 0)
        
        parent.pack_start(time_box, False, False, 0)

        time_fields = [self.start_h, self.start_m, self.start_s, self.start_ms,
                       self.end_h, self.end_m, self.end_s, self.end_ms]
        for field in time_fields:
            field.connect("value-changed", self.on_time_field_changed)

    # Setup progress bar
    def setup_progress_bar(self, parent):
        progress_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        progress_container.get_style_context().add_class("progress-container")
        
        self.percent_label = Gtk.Label(label="0%")
        self.percent_label.get_style_context().add_class("format-value")
        self.percent_label.set_halign(Gtk.Align.CENTER)
        progress_container.pack_start(self.percent_label, False, False, 0)
        
        self.progress = Gtk.ProgressBar()
        self.progress.get_style_context().add_class("progress-bar")
        progress_container.pack_start(self.progress, False, False, 0)
        
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.get_style_context().add_class("status-text")
        progress_container.pack_start(self.status_label, False, False, 0)
        
        parent.pack_start(progress_container, False, False, 0)

    # Helper functions
    def get_combo_item_count(self, combo):
        model = combo.get_model()
        if model:
            return len(model)
        return 0

    def file_filter(self):
        f = Gtk.FileFilter()
        f.set_name("Video files")
        for p in ("*.mp4", "*.mkv", "*.webm", "*.avi", "*.mov", "*.wmv", "*.flv", 
                 "*.m4v", "*.3gp", "*.mpg", "*.mpeg", "*.ts", "*.mts", "*.m2ts"):
            f.add_pattern(p)
        f.add_mime_type("video/*")
        return f

    def get_format_display_text(self):
        format_type = self.get_selected_format()
        
        audio_output = self.settings.get("audio_output_format", "mp3")
        
        if audio_output != "none":
            return f"AUDIO ONLY - {audio_output.upper()}"
        
        if format_type == "original":
            return "Original - Copy (No re-encoding)"
        
        video_codec = self.settings.get("video_codec", "H264")
        quality = self.settings.get("quality", "1080p")
        return f"{format_type.upper()} - {quality} {video_codec}"

    def get_selected_format(self):
        format_text = self.format_combo.get_active_text()
        if format_text is None:
            return "original"
            
        if " - " in format_text:
            return format_text.lower().split(" - ")[0]
        return format_text.lower()

    def get_settings(self):
        return {
            "format": self.get_selected_format(),
            "quality": self.settings.get("quality", "1080p"),
            "video_bitrate": self.settings.get("custom_bitrate", "4000"),
            "audio_quality": self.settings.get("audio_quality", "192"),
            "seek_step": 1.0,
            "fine_seek_step": 0.1,
            "action": self.action_combo.get_active(),
            "set_in_callback": self._set_in,
            "set_out_callback": self._set_out
        }

    # Event handlers
    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        if data.get_uris():
            uri = data.get_uris()[0]
            file_path = uri.replace('file://', '')
            file_path = GLib.filename_from_uri(uri)[0] if uri.startswith('file://') else file_path
            
            if is_video_file(file_path):
                self.filechooser.set_filename(file_path)
                self.on_file_selected(self.filechooser)
            else:
                self.show_error_dialog(
                    "Invalid Video File",
                    "Please drop a valid video file.\n\nSupported formats:\nMP4, MKV, WebM, AVI, MOV, WMV, FLV, etc."
                )

    def on_file_selected(self, chooser):
        path = chooser.get_filename()
        if not path: 
            return
        
        if not is_video_file(path):
            self.show_error_dialog(
                "Invalid Video File", 
                "Please select a valid video file.\n\nThe file either is not a video or is corrupted."
            )
            return
        
        self.player.set_file(path)
        
        try:
            duration_out = subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", path
            ], text=True, stderr=subprocess.DEVNULL)
            
            durf = float(duration_out.strip())
            h, m, s, ms = seconds_to_hmsms(durf)
            
            info_out = subprocess.check_output([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height",
                "-of", "default=noprint_wrappers=1", path
            ], text=True, stderr=subprocess.DEVNULL)
            
            info_lines = info_out.strip().split('\n')
            codec = info_lines[0] if len(info_lines) > 0 else "unknown"
            width = info_lines[1] if len(info_lines) > 1 else "0"
            height = info_lines[2] if len(info_lines) > 2 else "0"
            
            video_info = f"Duration: {h:02d}:{m:02d}:{s:02d}.{ms:03d} | Dimensions: {width}x{height} | Codec: {codec.upper()}"
            self.video_info_label.set_text(video_info)
            
            self.start_h.set_value(0); self.start_m.set_value(0); self.start_s.set_value(0); self.start_ms.set_value(0)
            self.end_h.set_value(h); self.end_m.set_value(m); self.end_s.set_value(s); self.end_ms.set_value(ms)
            
            self.player.in_position = 0.0
            self.player.out_position = 1.0
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            self.video_info_label.set_text("Duration: Unknown | Failed to load video details")
            self.start_h.set_value(0); self.start_m.set_value(0); self.start_s.set_value(0); self.start_ms.set_value(0)
            self.end_h.set_value(0); self.end_m.set_value(0); self.end_s.set_value(0); self.end_ms.set_value(0)
            self.player.in_position = 0.0
            self.player.out_position = 0.0

    def on_format_changed(self, combo):
        self.format_value_label.set_text(self.get_format_display_text())
        self.settings["format_index"] = combo.get_active()
        self.settings_manager.save_settings(self.settings)

    def on_settings_clicked(self, btn):
        from modules.settings import SettingsDialog
        dialog = SettingsDialog(self, self.settings, self.format_combo)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            self.settings = dialog.get_updated_settings()
            self.settings_manager.save_settings(self.settings)
            
            new_format_index = self.settings.get("format_index", 0)
            item_count = self.get_combo_item_count(self.format_combo)
            if new_format_index < item_count:
                self.format_combo.set_active(new_format_index)
            self.on_format_changed(self.format_combo)
        
        dialog.destroy()

    def on_export(self, button):
        self.export_manager.start_export()

    def on_abort(self, button):
        self.export_manager.abort_export()

    def on_quit_clicked(self, button):
        if self.is_processing:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text="Processing in Progress"
            )
            dialog.get_style_context().add_class("dialog")
            dialog.format_secondary_text(
                "A video processing operation is currently in progress.\n\n"
                "Exiting now will:\n"
                "• Stop the processing immediately\n"
                "• Delete the incomplete output file\n"
                "• Leave your source file untouched\n\n"
                "Are you sure you want to quit?"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK:
                self.force_quit_with_cleanup()
        else:
            Gtk.main_quit()

    def on_window_destroy(self, widget):
        if self.is_processing:
            self.force_quit_with_cleanup()
        else:
            Gtk.main_quit()

    def force_quit_with_cleanup(self):
        if self.is_processing:
            self.export_manager.abort_export()
            GLib.timeout_add(2000, Gtk.main_quit)
        else:
            Gtk.main_quit()

    def on_about_clicked(self, btn):
        about = Gtk.AboutDialog(transient_for=self, modal=True)
        about.get_style_context().add_class("dialog")
        about.set_program_name("NamaCut")
        about.set_version("2.0")
        about.set_comments("Video Cutter and Editor")
        about.set_authors(["Pourdaryaei"])
        about.set_website("https://pourdaryaei.ir")
        try:
            about.set_logo_icon_name("video-x-generic")
        except Exception:
            pass
        about.run()
        about.destroy()

    # Time management functions
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
            
            if self.player.duration:
                self.player.in_position = pos / self.player.duration

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

            if self.player.duration:
                self.player.out_position = pos / self.player.duration

    def on_time_field_changed(self, widget):
        start_seconds = hmsms_to_seconds(
            self.start_h.get_value_as_int(), 
            self.start_m.get_value_as_int(), 
            self.start_s.get_value_as_int(),
            self.start_ms.get_value_as_int()
        )
        end_seconds = hmsms_to_seconds(
            self.end_h.get_value_as_int(), 
            self.end_m.get_value_as_int(), 
            self.end_s.get_value_as_int(),
            self.end_ms.get_value_as_int()
        )
        
        if self.player.duration and self.player.duration > 0:
            self.player.update_markers_from_time_fields(start_seconds, end_seconds)

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

    # Dialog helpers
    def show_error_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.get_style_context().add_class("dialog")
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def show_info_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.get_style_context().add_class("dialog")
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


def main():
    """Main entry point for the application."""
    app = NamaCut()
    Gtk.main()

if __name__ == "__main__":
    main()
