import json
import os

# --------------------------------------------------
# Settings management
# --------------------------------------------------
class SettingsManager:
    def __init__(self):
        self.settings_file = os.path.join(os.path.expanduser("~"), ".namacut_settings.json")
    
    def load_settings(self):
        default_settings = {
            "format_index": 0,
            "video_codec": "H264",
            "resolution": "Original",
            "quality": "1080p",
            "crf_value": 23,
            "quality_slider": 6,
            "container": "MP4 (.mp4)",
            "video_audio_format": "AAC",
            "video_audio_bitrate": "192",
            "video_audio_quality": "192",  
            "audio_output_format": "none",
            "audio_quality": "192",   
            "action": 0
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    for key, value in saved_settings.items():
                        if key in default_settings:
                            default_settings[key] = value
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return default_settings
    
    def save_settings(self, settings):
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def reset_to_defaults(self):
        default_settings = self.load_settings()
        return self.save_settings(default_settings)