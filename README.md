#  NamaCut

**NamaCut** is a simple video trimming and conversion tool built with Python and GTK.  
It allows you to easily cut, preview, and convert videos using FFmpeg and GStreamer.

##  Screenshot

![NamaCut Screenshot](https://raw.githubusercontent.com/abdulhalim/NamaCut/refs/heads/main/screenshot.png)

---

##  Features
- Simple GTK interface   
- Trim and convert videos (MP4, MKV, WebM, MP3, AAC)  
- Real-time progress tracking  
- Built with Python 3 and GStreamer  
- Lightweight and fast 

---

##  How to Use

### 1 Install (Debian/Ubuntu)
Download the `.deb` package from the [Releases]([https://github.com/Pourdaryaei/NamaCut/releases](https://github.com/abdulhalim/NamaCut/releases)) page and install:

```bash
sudo dpkg -i namacut_1.0_all.deb
sudo apt install -f
```

Then run:
```bash
namacut
```

### 2 Run from Source
If you prefer to run directly from source:
```bash
python3 NamaCut.py
```

---

##  Requirements
- Python 3  
- GTK 3 (PyGObject)  
- FFmpeg  
- GStreamer plugins (`gstreamer1.0-plugins-good`, `gstreamer1.0-libav`)

---

##  License
Licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

##  Author
**Pourdaryaei**  
 [www.pourdaryaei.ir](https://www.pourdaryaei.ir)  
 Pourdaryaei@yandex.com
