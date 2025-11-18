# NamaCut

**NamaCut** is a simple yet powerful video cutter and editor built with Python and GTK.  
It allows you to easily cut, preview, rotate, crop, and convert videos using FFmpeg and GStreamer.

## Screenshot

![NamaCut Screenshot](https://raw.githubusercontent.com/YOUR_USERNAME/namacut/refs/heads/main/Screenshot_NC.png)

---

## Features

- Simple and modern GTK interface with a dark theme.
- Cut and trim videos with **millisecond precision**.
- **Rotate, flip, and crop** videos with live preview.
- **Drag-and-drop** support for video files.
- Export to multiple formats (MP4, MKV, WEBM, AVI, MOV, etc.).
- **Advanced export settings** for custom format, quality, and bitrate.
- Real-time progress tracking with percentage display.
- **Post-export actions** (show message, open folder, close app).
- Built with Python 3 and GStreamer.
- Lightweight and fast.

---

## How to Use

### 1. Install (Debian/Ubuntu - Recommended)

Download the latest `.deb` package from the [Releases](https://github.com/YOUR_USERNAME/namacut/releases) page and install:

```bash
sudo dpkg -i namacut_2.0-1_amd64.deb
sudo apt-get install -f
```

Then run from your terminal or application menu:
```bash
namacut
```

### 2. Run from Source

If you prefer to run directly from the source code:

1.  Clone the repository:
    ```bash
    git clone https://github.com/YOUR_USERNAME/namacut.git
    cd namacut
    ```
2.  Install dependencies:
    ```bash
    sudo apt-get install python3-gi gir1.2-gtk-3.0 gir1.2-gst-1.0 ffmpeg
    ```
3.  Run the application:
    ```bash
    python3 main.py
    ```

---

## Requirements

- Python 3
- GTK 3 (PyGObject)
- FFmpeg
- GStreamer plugins (`gstreamer1.0-plugins-good`, `gstreamer1.0-libav`)

---

## License

Licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## Author

**Pourdaryaei**  
[www.pourdaryaei.ir](https://www.pourdaryaei.ir)  
Pourdaryaei@yandex.com
