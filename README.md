# NamaCut - Video Cutter and Editor

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Launching the Application](#launching-the-application)
- [Uninstallation](#uninstallation)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

NamaCut is a simple, cross-platform video cutter and editor built with Python and PyQt5. It allows you to:
- Cut and trim video files
- Rotate, flip, and crop videos
- Export in various formats (MP4, MKV, WebM, MP3, AAC, FLAC)
- Process videos with FFmpeg in the background

## Prerequisites

Before installation, ensure you have:
- **Python 3.8 or higher**
- **pip** (Python package manager)
- **FFmpeg** (for video processing)

On Ubuntu/Debian, you can install prerequisites with:
```bash
sudo apt update
sudo apt install python3 python3-pip ffmpeg
```

## Installation

### Method 1: Automated Installation (Recommended)

1. Download or clone the NamaCut repository:
```bash
git clone <repository-url>
cd namacut
```

2. Make the installation script executable:
```bash
chmod +x install.sh
```

3. Run the installation script:
```bash
./install.sh
```

The installer will:
- Check for Python 3 and install python3-venv if needed
- Create a Python virtual environment
- Install all required dependencies
- Create a desktop entry
- Add "Open with NamaCut" to the right-click context menu
- Set up file associations for video files

### Method 2: Manual Installation

If you prefer manual installation:

1. Create a virtual environment:
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Make the start script executable:
```bash
chmod +x start.sh
```

## Launching the Application

You can launch NamaCut in several ways:

### Method 1: From Application Menu
- Search for "NamaCut" in your application menu/dashboard
- Click on the NamaCut icon

### Method 2: From Desktop (if shortcut was created)
- Double-click the "NamaCut" shortcut on your desktop

### Method 3: From Terminal
```bash
./start.sh
```

### Method 4: Using Right-Click Context Menu
- Right-click on any video file (MP4, MKV, AVI, MOV, etc.)
- Select "Open with NamaCut" from the context menu

### Method 5: Drag & Drop
- Drag a video file and drop it onto the NamaCut window

### Method 6: Command Line with File
```bash
./start.sh /path/to/video.mp4
```

## File Associations

After installation, NamaCut is associated with these video formats:
- **MP4** (.mp4, .m4v)
- **MKV** (.mkv)
- **AVI** (.avi)
- **MOV** (.mov, .qt)
- **WebM** (.webm)
- **WMV** (.wmv)
- **FLV** (.flv)
- **MPEG** (.mpeg, .mpg, .mpe)
- **3GPP** (.3gp, .3g2)
- **Ogg** (.ogv, .ogg)

## Uninstallation

### Method 1: Using Uninstall Script

1. Make the uninstall script executable (if not already):
```bash
chmod +x uninstall.sh
```

2. Run the uninstall script:
```bash
./uninstall.sh
```

This will remove:
- The virtual environment
- Desktop menu entry
- Desktop shortcut
- Context menu entries
- File associations

### Method 2: Manual Uninstallation

1. Remove the virtual environment:
```bash
rm -rf venv
```

2. Remove desktop entries:
```bash
rm -f ~/.local/share/applications/namacut.desktop
rm -f ~/Desktop/namacut.desktop
sudo rm -f /usr/share/applications/namacut.desktop
```

3. Remove context menu scripts:
```bash
rm -f ~/.local/share/nautilus/scripts/Open\ with\ NamaCut
rm -f ~/.local/share/kservices5/ServiceMenus/namacut.desktop
```

4. Update desktop database:
```bash
update-desktop-database ~/.local/share/applications
```

## Troubleshooting

### Issue: "Python not found"
**Solution:** Install Python 3.8 or higher:
```bash
sudo apt install python3
```

### Issue: "python3-venv not available"
**Solution:** Install python3-venv:
```bash
sudo apt install python3-venv
```

### Issue: "FFmpeg not found"
**Solution:** Install FFmpeg:
```bash
sudo apt install ffmpeg
```

### Issue: Desktop icon not showing
**Solution:**
1. Log out and log back in
2. Update icon cache:
```bash
sudo update-desktop-database
```

### Issue: Right-click menu not working
**Solution:**
1. Restart your file manager (nautilus, dolphin, thunar)
2. Log out and log back in
3. Run the context menu setup again:
```bash
./context-menu.sh
```

### Issue: "Cannot activate virtual environment"
**Solution:** Reinstall using the install script:
```bash
./install.sh
```

### Issue: Application crashes on startup
**Solution:**
1. Check dependencies:
```bash
pip list | grep -E "PyQt5|qtawesome|opencv"
```

2. Reinstall dependencies:
```bash
source venv/bin/activate
pip install --force-reinstall PyQt5 qtawesome opencv-python
```

## Development

If you want to contribute to NamaCut:

1. Clone the repository:
```bash
git clone <repository-url>
cd namacut
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
pip install pytest black flake8 mypy
```

4. Run tests:
```bash
pytest
```

5. Format code:
```bash
black .
```

## Directory Structure

```
namacut/
├── install.sh              # Installation script
├── start.sh               # Launch script
├── uninstall.sh           # Uninstallation script
├── main.py               # Main application
├── requirements.txt      # Python dependencies
├── namacut.svg          # Application icon
├── namacut.xml          # MIME type definitions
├── ui/                  # User interface files
│   ├── main_window.py
│   ├── widgets.py
│   ├── dialogs.py
│   ├── media_player.py
│   ├── crop_widget.py
│   └── advanced_settings.py
├── core/                # Core functionality
│   ├── video_processor.py
│   ├── video_transformer.py
│   ├── settings_manager.py
│   └── utils.py
└── img/                # Images and icons
```

## Output Locations

NamaCut saves output files in the following directories:

- **Video files**: `~/Videos/NamaCut_Output/`
- **Audio files**: `~/Music/NamaCut_Output/`

Files are automatically named to avoid overwriting existing files.

## Features

- **Video Cutting**: Precise cut/trim with millisecond accuracy
- **Transformations**: Rotate, flip, and crop videos
- **Multiple Formats**: Export to MP4, MKV, WebM, MP3, AAC, FLAC
- **Quality Settings**: Adjust resolution and compression
- **Drag & Drop**: Simple drag and drop interface
- **Progress Tracking**: Real-time export progress
- **Presets**: Quick access to common settings

## System Requirements

- **OS**: Linux, macOS
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB free space
- **Python**: 3.8 or higher
- **FFmpeg**: Latest version recommended

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Check console output for error messages
3. Ensure all dependencies are installed
4. Try reinstalling with `./install.sh`

## License

NamaCut is released under the MIT License. See LICENSE file for details.

## Author

Developed by Abdulhalim Pourdaryaei
Website: https://pourdaryaei.ir

---

**Note**: After installation, you may need to log out and log back in for all context menu changes to take effect.
