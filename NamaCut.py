#!/bin/bash
set -e

APP_NAME="namacut"
VERSION="1.1"
ARCH="all"
BUILD_DIR="deb_build"
PACKAGE_DIR="${BUILD_DIR}/${APP_NAME}_${VERSION}_${ARCH}"

echo "🔨 Building NamaCut DEB package..."

# پاکسازی و ایجاد دایرکتوری‌ها
rm -rf ${BUILD_DIR}
mkdir -p ${PACKAGE_DIR}/DEBIAN
mkdir -p ${PACKAGE_DIR}/usr/bin
mkdir -p ${PACKAGE_DIR}/usr/lib/namacut
mkdir -p ${PACKAGE_DIR}/usr/share/applications
mkdir -p ${PACKAGE_DIR}/usr/share/icons/hicolor/scalable/apps

# کپی اسکریپت اصلی
cp NamaCut.py ${PACKAGE_DIR}/usr/lib/namacut/

# فایل کنترل با وابستگی‌های حداقلی
cat > ${PACKAGE_DIR}/DEBIAN/control << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: video
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-gst-plugins-base-1.0, gstreamer1.0-plugins-good, gstreamer1.0-plugins-bad, gstreamer1.0-plugins-ugly, gstreamer1.0-libav
Suggests: ffmpeg, libavcodec-extra
Maintainer: Pourdaryaei <Pourdaryaei@yandex.com>
Homepage: https://www.pourdaryaei.ir
Installed-Size: 15
Description: Video trimming and conversion tool
 NamaCut is a simple GUI tool for trimming videos and converting between formats.
 Supports MP4, MKV, WebM, AAC, MP3 formats with quality settings.
 Features real-time progress tracking and seekable video player.
EOF

# اسکریپت post-install ساده‌تر
cat > ${PACKAGE_DIR}/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e

echo "Installing NamaCut..."

# آپدیت کش آیکون و دسکتاپ
if which gtk-update-icon-cache > /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi

if which update-desktop-database > /dev/null; then
    update-desktop-database -q 2>/dev/null || true
fi

echo "NamaCut v1.1 installed successfully!"
echo "If you have video codec issues, run: sudo apt install gstreamer1.0-libav"
echo "Visit: https://www.pourdaryaei.ir"
exit 0
EOF
chmod 755 ${PACKAGE_DIR}/DEBIAN/postinst

# اسکریپت pre-remove
cat > ${PACKAGE_DIR}/DEBIAN/prerm << 'EOF'
#!/bin/bash
set -e
echo "Removing NamaCut..."
exit 0
EOF
chmod 755 ${PACKAGE_DIR}/DEBIAN/prerm

# لانچر ساده‌تر
cat > ${PACKAGE_DIR}/usr/bin/namacut << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/usr/lib/namacut')

# اجرای مستقیم
exec(open('/usr/lib/namacut/NamaCut.py').read())
EOF
chmod 755 ${PACKAGE_DIR}/usr/bin/namacut

# فایل دسکتاپ
cat > ${PACKAGE_DIR}/usr/share/applications/namacut.desktop << EOF
[Desktop Entry]
Name=NamaCut
Comment=Video trimming and conversion tool
Exec=namacut
Icon=vidcutter
Terminal=false
Type=Application
Categories=AudioVideo;Video;
Keywords=video;trim;cut;convert;editor;namacut;
StartupNotify=true
X-GNOME-UsesNotifications=true
EOF

# آیکون SVG
cat > ${PACKAGE_DIR}/usr/share/icons/hicolor/scalable/apps/vidcutter.svg << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4a86e8"/>
      <stop offset="100%" stop-color="#3a76d8"/>
    </linearGradient>
  </defs>
  
  <rect width="64" height="64" fill="url(#bg)" rx="12" ry="12"/>
  
  <!-- نمایشگر ویدئو -->
  <rect x="8" y="12" width="48" height="28" fill="#1a1a1a" rx="3" ry="3"/>
  <rect x="12" y="16" width="40" height="20" fill="#333" rx="2" ry="2"/>
  
  <!-- علامت پلی -->
  <polygon points="24,20 24,28 30,24" fill="#4a86e8"/>
  
  <!-- ابزار برش -->
  <rect x="16" y="44" width="32" height="4" fill="#fff" rx="2" ry="2"/>
  <rect x="20" y="48" width="8" height="8" fill="#fff" rx="1" ry="1"/>
  <rect x="36" y="48" width="8" height="8" fill="#fff" rx="1" ry="1"/>
  
  <!-- علامت قیچی -->
  <line x1="28" y1="44" x2="32" y2="52" stroke="#4a86e8" stroke-width="2"/>
  <line x1="32" y1="44" x2="28" y2="52" stroke="#4a86e8" stroke-width="2"/>
</svg>
EOF

# ساخت بسته
echo "Building DEB package..."
dpkg-deb --build ${PACKAGE_DIR}

echo "✅ DEB package built: ${PACKAGE_DIR}.deb"
echo ""
echo "📦 Installation:"
echo "   sudo dpkg -i ${PACKAGE_DIR}.deb"
echo ""
echo "🔧 If video issues occur, install only essential codec:"
echo "   sudo apt install gstreamer1.0-libav"
echo ""
echo "🎯 Usage: namacut"
