"""
Core module for NamaCut Video Editor

This module contains the core functionality including:
- Video processing and export
- Video transformations (rotate, flip, crop)
- Settings management
- Utility functions
"""


from .video_processor import VideoProcessor
from .video_transformer import VideoTransformer
from .settings_manager import SettingsManager
from .utils import (
    seconds_to_hmsms,
    hmsms_str,
    hmsms_to_seconds,
    get_file_type,
    is_video_file,
    get_output_directory,
    unique_output_path,
    cleanup_incomplete_files,
    parse_ffmpeg_progress
)

__all__ = [
    'VideoProcessor',
    'VideoTransformer', 
    'SettingsManager',
    'seconds_to_hmsms',
    'hmsms_str',
    'hmsms_to_seconds',
    'get_file_type',
    'is_video_file',
    'get_output_directory',
    'unique_output_path',
    'cleanup_incomplete_files',
    'parse_ffmpeg_progress'
]
