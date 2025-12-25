#!/usr/bin/env python3
"""
NamaCut - Video Cutter and Editor
Author: Pourdaryaei
License: MIT-X11
"""

import sys
import os
import warnings
import argparse
from pathlib import Path

# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------
# MUST be at the very top, before any Qt imports
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['QT_QUICK_BACKEND'] = 'software'
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.*=false'

# For Wayland (if user is using Wayland)
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    os.environ['QT_QPA_PLATFORM'] = 'wayland'

# --------------------------------------------------
# Application Constants
# --------------------------------------------------
APP_VERSION = "2.0.26"
APP_NAME = "NamaCut"
WEBSITE = "https://pourdaryaei.ir"

# --------------------------------------------------
# Command Line Interface Functions
# --------------------------------------------------
def show_version():
    """
    Display version information.
    """
    print(f"{APP_NAME} v{APP_VERSION}")
    print("Video Cutter and Editor")
    print(f"Author: Pourdaryaei")
    print(f"Website: {WEBSITE}")
    print("License: MIT-X11")

def show_help():
    """
    Display help information.
    """
    print(f"\nUsage: {os.path.basename(sys.argv[0])} [OPTIONS] [FILE]")
    print("\nOptions:")
    print("  FILE                    Video file to open (via right-click or drag & drop)")
    print("  -h, --help              Show this help message")
    print("  -v, --version           Show version information")
    print("  --debug                 Enable debug mode")
    print("\nExamples:")
    print(f"  {os.path.basename(sys.argv[0])} video.mp4      Open video.mp4")
    print(f"  {os.path.basename(sys.argv[0])} --version      Show version")
    print(f"  {os.path.basename(sys.argv[0])} --help         Show help")

def check_dependencies():
    """
    Check for required dependencies (ffmpeg and ffprobe).
    
    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    missing_deps = []
    
    # Check for ffmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            missing_deps.append("ffmpeg")
    except FileNotFoundError:
        missing_deps.append("ffmpeg")
    
    # Check for ffprobe
    try:
        result = subprocess.run(['ffprobe', '-version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            missing_deps.append("ffprobe")
    except FileNotFoundError:
        missing_deps.append("ffprobe")
    
    if missing_deps:
        print("ERROR: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install missing dependencies:")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  Fedora: sudo dnf install ffmpeg")
        print("  Arch: sudo pacman -S ffmpeg")
        return False
    
    return True

# --------------------------------------------------
# Main Application Entry Point
# --------------------------------------------------
def main():
    """
    Main entry point for the NamaCut application.
    """
    # Suppress deprecation warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # --------------------------------------------------
    # Command Line Argument Parsing
    # --------------------------------------------------
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - Video Cutter and Editor",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {os.path.basename(sys.argv[0])} video.mp4      Open video.mp4
  {os.path.basename(sys.argv[0])} --version      Show version info
  {os.path.basename(sys.argv[0])} --help         Show this help

Website: {WEBSITE}
        """
    )
    
    # Define command line arguments
    parser.add_argument(
        'file', 
        nargs='?', 
        help='Video file to open (optional)'
    )
    
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show this help message'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version information'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    # For compatibility with older versions
    parser.add_argument(
        '-V', 
        action='store_true',
        help='Show version information (same as --version)',
        dest='version_compat'
    )
    
    args = parser.parse_args()
    
    # --------------------------------------------------
    # Handle Command Line Options
    # --------------------------------------------------
    # Handle help
    if args.help or '-h' in sys.argv or '--help' in sys.argv:
        show_help()
        sys.exit(0)
    
    # Handle version
    if args.version or args.version_compat or '-v' in sys.argv or '--version' in sys.argv:
        show_version()
        sys.exit(0)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Enable debug if requested
    if args.debug:
        os.environ['QT_LOGGING_RULES'] = '*.debug=true'
        print(f"DEBUG MODE ENABLED - {APP_NAME} v{APP_VERSION}")
    
    # Validate file if provided
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File not found: {args.file}")
            print("Please check the file path and try again.")
            sys.exit(1)
        
        if not file_path.is_file():
            print(f"ERROR: Not a file: {args.file}")
            sys.exit(1)
    
    # --------------------------------------------------
    # Qt Application Setup
    # --------------------------------------------------
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer, Qt
        from PyQt5.QtGui import QIcon
    except ImportError as e:
        print(f"ERROR: Failed to import PyQt5: {e}")
        print("\nPlease install PyQt5:")
        print("  pip install PyQt5")
        print("  or")
        print("  Ubuntu/Debian: sudo apt install python3-pyqt5")
        print("  Fedora: sudo dnf install python3-qt5")
        print("  Arch: sudo pacman -S python-pyqt5")
        sys.exit(1)
    
    # Create QApplication instance
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Pourdaryaei")
    
    # Set application icon if available
    icon_path = Path(__file__).parent / "img" / "logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Set application style
    app.setStyle("Fusion")
    
    # --------------------------------------------------
    # Main Window Creation (Delayed for threading issues)
    # --------------------------------------------------
    def create_app():
        """
        Create and configure the main application window.
        
        Returns:
            VideoEditor: The main application window instance
        """
        from ui.main_window import VideoEditor
        
        try:
            editor = VideoEditor()
            
            # Load video file if provided via command line
            if args.file:
                # Convert to absolute path
                video_path = str(Path(args.file).resolve())
                
                # Small delay to ensure UI is ready
                def load_video():
                    success = editor.load_video_file(video_path)
                    if not success:
                        print(f"Warning: Could not load video: {video_path}")
                
                QTimer.singleShot(300, load_video)
            
            editor.show()
            
            # Center window on screen
            screen_geometry = app.primaryScreen().availableGeometry()
            x = (screen_geometry.width() - editor.width()) // 2
            y = (screen_geometry.height() - editor.height()) // 2
            editor.move(x, y)
            
            return editor
            
        except Exception as e:
            print(f"ERROR: Failed to create application window: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            app.quit()
            sys.exit(1)
    
    # Create main window
    editor = create_app()
    
    # --------------------------------------------------
    # Application Execution and Cleanup
    # --------------------------------------------------
    exit_code = app.exec_()
    
    # Cleanup before exit
    if hasattr(editor, 'video_processor'):
        editor.video_processor.abort_processing()
    
    sys.exit(exit_code)

# --------------------------------------------------
# Script Entry Point
# --------------------------------------------------
if __name__ == '__main__':
    main()
# main.py