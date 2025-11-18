# settings.py
import gi
import json
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk

# Settings File Manager
class SettingsManager:
    def __init__(self):
        self.settings_file = os.path.join(os.path.expanduser("~"), ".namacut_settings.json")
    
    def load_settings(self):
        default_settings = {
            "format_index": 0,
            "video_codec": "H264",
            "quality": "1080p",
            "bitrate_type": "Auto",
            "custom_bitrate": "4000",
            "vbr_value": 23,
            "video_audio_format": "AAC",
            "video_audio_quality": "192",
            "audio_output_format": "mp3",
            "audio_quality": "192",
            "flac_compression_level": "5",
            "action": 0
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    default_settings.update(saved_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return default_settings
    
    def save_settings(self, settings):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

# Settings Dialog UI
class SettingsDialog:
    def __init__(self, parent, settings, format_combo):
        self.parent = parent
        self.settings = settings.copy()
        self.format_combo = format_combo
        self.current_tab = 0
        
        self.dialog = Gtk.Dialog(title="Output Settings", transient_for=parent, modal=True)
        self.dialog.set_default_size(500, 430)
        
        self.apply_dialog_css()
        
        self.setup_ui()
        self.update_ui_state()
    
    # Apply Custom CSS
    def apply_dialog_css(self):
        css_provider = Gtk.CssProvider()
        css = """
        .dialog { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog > box { background-color: #1e1e2e; color: #cdd6f4; font-size: 0.9em; }
        .dialog .content-area { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog .action-area { background-color: #1e1e2e; border-top: 1px solid #313244; }
        .dialog notebook { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog notebook > stack > box { background-color: #1e1e2e; color: #cdd6f4; }
        .dialog button { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px 10px; }
        .dialog button:hover { background-color: #45475a; }
        .dialog combobox { background-color: #313244; color: #cdd6f4; }
        .dialog combobox box { background-color: #313244; color: #cdd6f4; }
        .dialog entry { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 3px 6px; }
        .dialog scale { background-color: #313244; color: #cdd6f4; }
        .dialog scale trough { background-color: #45475a; border-radius: 4px; min-height: 5px; }
        .dialog scale trough highlight { background-color: #89b4fa; border-radius: 4px; min-height: 5px; }
        .dialog scale trough slider { background-color: #89b4fa; border: 2px solid #cdd6f4; border-radius: 50%; min-width: 10px; min-height: 10px; margin: -5px; }
        .dialog label { color: #cdd6f4; }
        .section-title { color: #cdd6f4; font-weight: bold; font-size: 12px; margin-bottom: 6px; }
        .info-label { color: #a6adc8; font-style: italic; font-size: 11px; }
        """
        css_provider.load_from_data(css.encode('utf-8'))
        
        screen = Gdk.Screen.get_default()
        style_context = self.dialog.get_style_context()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    # Setup Dialog UI
    def setup_ui(self):
        content_area = self.dialog.get_content_area()
        content_area.set_border_width(8)
        
        self.notebook = Gtk.Notebook()
        self.notebook.connect("switch-page", self.on_tab_switched)
        
        video_tab = self.create_video_tab()
        self.notebook.append_page(video_tab, Gtk.Label(label="Video Export"))
        
        audio_tab = self.create_audio_tab()
        self.notebook.append_page(audio_tab, Gtk.Label(label="Audio Only Export"))
        
        content_area.pack_start(self.notebook, True, True, 0)
        
        action_area = self.dialog.get_action_area()
        action_area.set_spacing(4)
        
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda w: self.dialog.response(Gtk.ResponseType.CANCEL))
        
        save_btn = Gtk.Button(label="Save Settings")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self.on_save_clicked)
        
        action_area.pack_start(cancel_btn, False, False, 0)
        action_area.pack_end(save_btn, False, False, 0)
        
        self.dialog.show_all()
        
        if self.settings.get("audio_output_format", "none") != "none":
            self.notebook.set_current_page(1)
            self.current_tab = 1

    # Create Video Export Tab
    def create_video_tab(self):
        video_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        video_tab.set_border_width(6)
        
        format_frame = self.create_section("Output Format", video_tab)
        self.preset_combo = Gtk.ComboBoxText()
        formats = [
            ("Original - Copy", "original"), ("MP4", "mp4"), ("MKV", "mkv"), ("WEBM", "webm"), 
            ("AVI", "avi"), ("MOV", "mov"), ("WMV", "wmv"), ("FLV", "flv"), ("MPEG", "mpeg"), ("TS", "ts")
        ]
        for label, _ in formats:
            self.preset_combo.append_text(label)
        self.preset_combo.set_active(self.settings.get("format_index", 0))
        self.preset_combo.connect("changed", self.on_preset_changed)
        format_frame.add(self.preset_combo)

        codec_frame = self.create_section("Video Codec", video_tab)
        self.video_codec_combo = Gtk.ComboBoxText()
        self.all_codecs = [
            ("H.264 (Recommended)", "H264"), ("H.265 (HEVC)", "H265"), 
            ("VP9 (WebM)", "VP9"), ("AV1 (Modern)", "AV1")           
        ]
        for label, _ in self.all_codecs:
            self.video_codec_combo.append_text(label)
        
        current_codec = self.settings.get("video_codec", "H264")
        codec_index = next((i for i, (_, codec) in enumerate(self.all_codecs) if codec == current_codec), 0)
        self.video_codec_combo.set_active(codec_index)
        self.video_codec_combo.connect("changed", self.on_video_codec_changed)
        codec_frame.add(self.video_codec_combo)

        quality_frame = self.create_section("Video Quality", video_tab)
        self.quality_combo = Gtk.ComboBoxText()
        qualities = ["Original", "4K", "2K", "1080p", "720p", "480p"]
        for quality in qualities:
            self.quality_combo.append_text(quality)
        
        current_quality = self.settings.get("quality", "1080p")
        quality_index = qualities.index(current_quality) if current_quality in qualities else 3
        self.quality_combo.set_active(quality_index)
        quality_frame.add(self.quality_combo)

        bitrate_frame = self.create_section("Video Quality Settings", video_tab)
        bitrate_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        bitrate_type_box = Gtk.Box(spacing=6)
        bitrate_type_label = Gtk.Label(label="Bitrate Type:")
        self.bitrate_type_combo = Gtk.ComboBoxText()
        bitrate_type_options = ["Auto", "Custom", "VBR (CRF)"]
        for btype in bitrate_type_options:
            self.bitrate_type_combo.append_text(btype)
        
        current_bitrate_type_value = self.settings.get("bitrate_type", "Auto")
        bitrate_type_map = {"Auto": "Auto", "Custom": "Custom", "VBR": "VBR (CRF)"}
        current_bitrate_type_display = bitrate_type_map.get(current_bitrate_type_value, "Auto")
        
        try:
            bitrate_type_index = bitrate_type_options.index(current_bitrate_type_display)
        except ValueError:
            bitrate_type_index = 0
        self.bitrate_type_combo.set_active(bitrate_type_index)
        
        self.bitrate_type_combo.connect("changed", self.on_bitrate_type_changed)
        
        bitrate_type_box.pack_start(bitrate_type_label, False, False, 0)
        bitrate_type_box.pack_start(self.bitrate_type_combo, True, True, 0)
        bitrate_box.pack_start(bitrate_type_box, False, False, 0)

        self.custom_bitrate_box = Gtk.Box(spacing=6)
        custom_bitrate_label = Gtk.Label(label="Custom Bitrate (kbps):")
        self.custom_bitrate_entry = Gtk.Entry()
        self.custom_bitrate_entry.set_text(self.settings.get("custom_bitrate", "4000"))
        self.custom_bitrate_entry.set_size_request(80, -1)
        
        self.custom_bitrate_box.pack_start(custom_bitrate_label, False, False, 0)
        self.custom_bitrate_box.pack_start(self.custom_bitrate_entry, False, False, 0)
        bitrate_box.pack_start(self.custom_bitrate_box, False, False, 0)

        self.vbr_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        
        self.vbr_label = Gtk.Label()
        self.vbr_label.set_halign(Gtk.Align.START)
        
        self.vbr_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 51, 1)
        self.vbr_slider.set_value(self.settings.get("vbr_value", 23))
        self.vbr_slider.set_draw_value(False)
        self.vbr_slider.connect("value-changed", self.on_vbr_slider_changed)
        
        self.vbr_value_label = Gtk.Label()
        self.vbr_value_label.set_halign(Gtk.Align.CENTER)
        
        self.vbr_box.pack_start(self.vbr_label, False, False, 0)
        self.vbr_box.pack_start(self.vbr_slider, True, True, 0)
        self.vbr_box.pack_start(self.vbr_value_label, False, False, 0)
        
        bitrate_box.pack_start(self.vbr_box, False, False, 0)
        bitrate_frame.add(bitrate_box)

        audio_frame = self.create_section("Audio Settings for Video", video_tab)
        audio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        audio_format_box = Gtk.Box(spacing=6)
        audio_format_label = Gtk.Label(label="Audio Format:")
        self.video_audio_format_combo = Gtk.ComboBoxText()
        video_audio_format_options = ["Copy Original", "AAC (Recommended)", "MP3", "AC3 (Surround)"]
        for format_name in video_audio_format_options:
            self.video_audio_format_combo.append_text(format_name)
        
        current_audio_format_value = self.settings.get("video_audio_format", "AAC")
        video_audio_format_map = {
            "Copy Original": "Copy Original", "AAC": "AAC (Recommended)",
            "MP3": "MP3", "AC3": "AC3 (Surround)"
        }
        current_audio_format_display = video_audio_format_map.get(current_audio_format_value, "AAC (Recommended)")
        
        try:
            format_index = video_audio_format_options.index(current_audio_format_display)
        except ValueError:
            format_index = 1
        self.video_audio_format_combo.set_active(format_index)
        
        self.video_audio_format_combo.connect("changed", self.on_video_audio_format_changed)
        audio_format_box.pack_start(audio_format_label, False, False, 0)
        audio_format_box.pack_start(self.video_audio_format_combo, True, True, 0)
        audio_box.pack_start(audio_format_box, False, False, 0)
        
        self.video_audio_quality_box = Gtk.Box(spacing=6)
        video_audio_quality_label = Gtk.Label(label="Audio Quality:")
        self.video_audio_quality_combo = Gtk.ComboBoxText()
        
        self.update_video_audio_quality_options(current_audio_format_value)
        
        self.video_audio_quality_box.pack_start(video_audio_quality_label, False, False, 0)
        self.video_audio_quality_box.pack_start(self.video_audio_quality_combo, True, True, 0)
        audio_box.pack_start(self.video_audio_quality_box, False, False, 0)
        
        audio_frame.add(audio_box)

        return video_tab

    # Create Audio Only Export Tab
    def create_audio_tab(self):
        audio_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        audio_tab.set_border_width(6)
        
        info_label = Gtk.Label(label="Export audio only (without video)")
        info_label.get_style_context().add_class("info-label")
        audio_tab.pack_start(info_label, False, False, 0)

        format_frame = self.create_section("Audio Format", audio_tab)
        self.audio_output_combo = Gtk.ComboBoxText()
        audio_formats = [
            ("MP3 Audio", "mp3"), ("AAC Audio", "aac"), 
            ("WAV Audio", "wav"), ("FLAC Audio", "flac")
        ]
        for label, _ in audio_formats:
            self.audio_output_combo.append_text(label)
        
        current_audio_output = self.settings.get("audio_output_format", "mp3")
        output_index = next((i for i, (_, fmt) in enumerate(audio_formats) if fmt == current_audio_output), 0)
        self.audio_output_combo.set_active(output_index)
        self.audio_output_combo.connect("changed", self.on_audio_format_changed)
        format_frame.add(self.audio_output_combo)

        self.audio_quality_frame = self.create_section("Audio Quality", audio_tab)
        self.audio_only_quality_combo = Gtk.ComboBoxText()
        
        self.update_audio_quality_options(current_audio_output)
        
        self.audio_quality_frame.add(self.audio_only_quality_combo)

        return audio_tab

    # Create a Framed Section
    def create_section(self, title, parent):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.set_margin_bottom(6)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        
        title_label = Gtk.Label(label=title)
        title_label.get_style_context().add_class("section-title")
        title_label.set_halign(Gtk.Align.START)
        box.pack_start(title_label, False, False, 0)
        
        frame.add(box)
        parent.pack_start(frame, False, False, 0)
        return box

    # Update UI State
    def update_ui_state(self):
        is_original = (self.preset_combo.get_active_text() == "Original - Copy")
        
        sections_to_disable = [
            self.video_codec_combo, self.quality_combo, 
            self.bitrate_type_combo, self.video_audio_format_combo, self.video_audio_quality_combo
        ]
        
        for widget in sections_to_disable:
            widget.set_sensitive(not is_original)
        
        self.on_bitrate_type_changed()
        self.on_video_codec_changed()

    # Tab Switch Handler
    def on_tab_switched(self, notebook, page, page_num):
        self.current_tab = page_num

    # Preset Change Handler
    def on_preset_changed(self, combo):
        self.update_ui_state()
        self.update_codec_compatibility()

    # Update Codec Compatibility
    def update_codec_compatibility(self):
        format_type = self._get_format_from_index(self.preset_combo.get_active())
        
        self.video_codec_combo.remove_all()
        
        if format_type == "webm":
            codecs = [("VP9 (WebM)", "VP9"), ("AV1 (Modern)", "AV1")]
        elif format_type in ["mov", "flv", "wmv"]:
            codecs = [("H.264 (Recommended)", "H264")]
        else:
            codecs = self.all_codecs
        
        for label, value in codecs:
            self.video_codec_combo.append_text(label)
        
        self.video_codec_combo.set_active(0)

    def _get_format_from_index(self, index):
        formats = ["original", "mp4", "mkv", "webm", "avi", "mov", "wmv", "flv", "mpeg", "ts"]
        return formats[index] if index < len(formats) else "original"

    # Video Codec Change Handler
    def on_video_codec_changed(self, combo=None):
        try:
            codec_text = self.video_codec_combo.get_active_text() or "H.264 (Recommended)"
            
            if "VP9" in codec_text or "AV1" in codec_text:
                self.vbr_slider.set_range(0, 63)
                self.vbr_label.set_text("CRF Value (0-63):")
            else:
                self.vbr_slider.set_range(0, 51)
                self.vbr_label.set_text("CRF Value (0-51):")
            
            self.on_vbr_slider_changed()
        except Exception as e:
            print(f"Error in video codec changed: {e}")

    # Bitrate Type Change Handler
    def on_bitrate_type_changed(self, combo=None):
        active_type = self.bitrate_type_combo.get_active_text() or "Auto"
        
        is_vbr_visible = "VBR" in active_type
        
        self.custom_bitrate_box.set_visible(active_type == "Custom")
        self.vbr_box.set_visible(is_vbr_visible)

    # VBR Slider Change Handler
    def on_vbr_slider_changed(self, slider=None):
        try:
            value = int(self.vbr_slider.get_value())
            
            if value <= 18: quality_text = "Very High"
            elif value <= 23: quality_text = "High"
            elif value <= 28: quality_text = "Medium"
            elif value <= 35: quality_text = "Low"
            else: quality_text = "Very Low"
            
            file_size_desc = self._estimate_file_size_description(value)
            self.vbr_value_label.set_markup(
                f"<b>CRF: {value}</b> - {quality_text} | 📁 {file_size_desc}"
            )
            
            self.vbr_slider.set_tooltip_text(f"Lower CRF = Higher quality, larger file")
            
        except Exception as e:
            print(f"Error in VBR slider changed: {e}")
    
    def _estimate_file_size_description(self, crf_value):
        if crf_value <= 18: return "Very Large"
        elif crf_value <= 23: return "Medium"
        elif crf_value <= 28: return "Small"
        else: return "Very Small"

    # Video Audio Format Change Handler
    def on_video_audio_format_changed(self, combo):
        format_text = combo.get_active_text()
        format_value = "AAC"
        
        if "Copy" in format_text: format_value = "Copy Original"
        elif "MP3" in format_text: format_value = "MP3"
        elif "AC3" in format_text: format_value = "AC3"
        else: format_value = "AAC"
        
        self.update_video_audio_quality_options(format_value)

    # Update Video Audio Quality Options
    def update_video_audio_quality_options(self, format_value):
        self.video_audio_quality_combo.remove_all()
        
        if format_value == "Copy Original":
            self.video_audio_quality_combo.append_text("Same as source")
            self.video_audio_quality_combo.set_sensitive(False)
        elif format_value == "AC3":
            for bitrate in ["224", "384", "448", "640"]:
                description = f"{bitrate} kbps"
                if bitrate == "384": description += " (Recommended)"
                elif bitrate == "640": description += " (High Quality)"
                self.video_audio_quality_combo.append_text(description)
            self.video_audio_quality_combo.set_sensitive(True)
        else:
            for bitrate in ["128", "192", "256", "320"]:
                description = f"{bitrate} kbps"
                if bitrate == "192": description += " (Recommended)"
                elif bitrate == "320": description += " (High Quality)"
                self.video_audio_quality_combo.append_text(description)
            self.video_audio_quality_combo.set_sensitive(True)
        
        if format_value == "Copy Original":
            self.video_audio_quality_combo.set_active(0)
        elif format_value == "AC3":
            self.video_audio_quality_combo.set_active(1)
        else:
            self.video_audio_quality_combo.set_active(1)

    # Audio Format Change Handler
    def on_audio_format_changed(self, combo):
        format_text = combo.get_active_text()
        format_value = "mp3"
        
        if "AAC" in format_text: format_value = "aac"
        elif "WAV" in format_text: format_value = "wav"
        elif "FLAC" in format_text: format_value = "flac"
        
        self.update_audio_quality_options(format_value)

    # Update Audio Quality Options
    def update_audio_quality_options(self, format_value):
        self.audio_only_quality_combo.remove_all()
        
        if format_value == "wav":
            self.audio_only_quality_combo.append_text("Uncompressed (Lossless)")
            self.audio_only_quality_combo.set_sensitive(False)
        elif format_value == "flac":
            for level in range(9):
                description = f"Level {level}"
                if level == 0: description += " (Fastest)"
                elif level == 8: description += " (Best Compression)"
                self.audio_only_quality_combo.append_text(description)
            self.audio_only_quality_combo.set_sensitive(True)
            
            current_level = self.settings.get("flac_compression_level", "5")
            try:
                level_index = int(current_level)
                if 0 <= level_index <= 8:
                    self.audio_only_quality_combo.set_active(level_index)
                else:
                    self.audio_only_quality_combo.set_active(5)
            except ValueError:
                self.audio_only_quality_combo.set_active(5)
        else:
            for bitrate in ["64", "128", "192", "256", "320"]:
                description = f"{bitrate} kbps"
                if bitrate == "192": description += " (Recommended)"
                elif bitrate == "320": description += " (High Quality)"
                self.audio_only_quality_combo.append_text(description)
            self.audio_only_quality_combo.set_sensitive(True)
            
            current_quality = self.settings.get("audio_quality", "192")
            if current_quality in ["64", "128", "192", "256", "320"]:
                quality_index = ["64", "128", "192", "256", "320"].index(current_quality)
                self.audio_only_quality_combo.set_active(quality_index)
            else:
                self.audio_only_quality_combo.set_active(2)

    # Save Button Handler
    def on_save_clicked(self, widget):
        try:
            if self.current_tab == 0:
                audio_output_value = "none"
                
                video_audio_format_text = self.video_audio_format_combo.get_active_text()
                video_audio_format_value = "AAC"
                if "Copy" in video_audio_format_text: video_audio_format_value = "Copy Original"
                elif "MP3" in video_audio_format_text: video_audio_format_value = "MP3"
                elif "AC3" in video_audio_format_text: video_audio_format_value = "AC3"
                
                if video_audio_format_value == "Copy Original":
                    video_audio_quality_value = "Copy"
                else:
                    video_audio_quality_text = self.video_audio_quality_combo.get_active_text()
                    video_audio_quality_value = video_audio_quality_text.split(" ")[0] if video_audio_quality_text else "192"
            else:
                audio_output_text = self.audio_output_combo.get_active_text()
                audio_output_value = "mp3"
                if "AAC" in audio_output_text: audio_output_value = "aac"
                elif "WAV" in audio_output_text: audio_output_value = "wav"
                elif "FLAC" in audio_output_text: audio_output_value = "flac"
                
                if audio_output_value == "flac":
                    quality_text = self.audio_only_quality_combo.get_active_text()
                    flac_level = 5
                    try:
                        flac_level = int(quality_text.split()[1])
                    except (ValueError, IndexError):
                        pass
                    audio_quality_value = str(flac_level)
                elif audio_output_value == "wav":
                    audio_quality_value = "N/A"
                else:
                    audio_quality_text = self.audio_only_quality_combo.get_active_text()
                    audio_quality_value = audio_quality_text.split(" ")[0] if audio_quality_text else "192"
                
                video_audio_format_value = "AAC"
                video_audio_quality_value = "192"
            
            selected_codec_text = self.video_codec_combo.get_active_text() or "H.264 (Recommended)"
            selected_codec = "H264"
            for label, value in self.all_codecs:
                if label in selected_codec_text:
                    selected_codec = value
                    break
            
            self.settings.update({
                "format_index": self.preset_combo.get_active(),
                "video_codec": selected_codec,
                "quality": self.quality_combo.get_active_text(),
                "bitrate_type": self.bitrate_type_combo.get_active_text(),
                "custom_bitrate": self.custom_bitrate_entry.get_text(),
                "vbr_value": int(self.vbr_slider.get_value()),
                "video_audio_format": video_audio_format_value,
                "video_audio_quality": video_audio_quality_value,
                "audio_output_format": audio_output_value,
                "audio_quality": audio_quality_value if self.current_tab == 1 else self.settings.get("audio_quality", "192")
            })
            
            if audio_output_value == "flac":
                quality_text = self.audio_only_quality_combo.get_active_text()
                try:
                    flac_level = int(quality_text.split()[1])
                    self.settings["flac_compression_level"] = str(flac_level)
                except (ValueError, IndexError):
                    self.settings["flac_compression_level"] = "5"
            
            self.dialog.response(Gtk.ResponseType.OK)
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error saving settings"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()

    # Get Updated Settings
    def get_updated_settings(self):
        return self.settings

    # Run Dialog
    def run(self):
        return self.dialog.run()

    # Destroy Dialog
    def destroy(self):
        self.dialog.destroy()
