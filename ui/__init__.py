# ui/__init__.py
# --------------------------------------------------
# UI Package Initialization
# --------------------------------------------------

# Import main classes for easier access
from .main_window import VideoEditor
from .dialogs import SettingsDialog, AboutDialog
from .advanced_settings import AdvancedSettingsDialog
from .widgets import IconButton, VideoPlayer
from .media_player import MediaPlayer
from .crop_widget import CropOverlay

# Optional: Define what gets imported with "from ui import *"
__all__ = [
    'VideoEditor',
    'SettingsDialog',
    'AboutDialog',
    'AdvancedSettingsDialog',
    'IconButton',
    'VideoPlayer',
    'MediaPlayer',
    'CropOverlay'
]