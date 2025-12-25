#!/bin/bash

# NamaCut Video Editor - Installation Script
# Author: Pourdaryaei
# License: MIT

set -e  # Exit on error

# Configuration
APP_NAME="NamaCut"
APP_VERSION="2.0.26"
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
MAIN_PY="main.py"
ICON_FILE="namacut.svg"
DESKTOP_FILE="namacut.desktop"
START_SCRIPT="start.sh"
MIME_FILE="namacut.xml"

# Get absolute path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_message() {
    echo -e "${BLUE}[${APP_NAME}]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check Python installation
check_python() {
    print_message "Checking Python installation..."
    
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
        print_success "Python 3 found"
    elif command -v python &>/dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1)
        if [[ "$PYTHON_VERSION" -eq 3 ]]; then
            PYTHON_CMD="python"
            print_success "Python 3 found"
        else
            print_error "Python 3 is required but not found"
            exit 1
        fi
    else
        print_error "Python is not installed. Please install Python 3.8 or higher"
        print_message "Install with: sudo apt install python3 python3-pip"
        exit 1
    fi
}

# Install python3-venv if needed
install_python_venv() {
    print_message "Checking for python3-venv package..."
    
    if $PYTHON_CMD -c "import venv" &>/dev/null; then
        print_success "python3-venv is available"
        return 0
    fi
    
    print_warning "python3-venv is not available. Installing..."
    
    # Detect distribution
    if [[ -f /etc/debian_version ]]; then
        # Debian/Ubuntu
        sudo apt update
        sudo apt install -y python3-venv
    elif [[ -f /etc/redhat-release ]]; then
        # RedHat/Fedora
        sudo dnf install -y python3-virtualenv
    elif [[ -f /etc/arch-release ]]; then
        # Arch
        sudo pacman -S --noconfirm python-virtualenv
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_message "On macOS, venv should be included with Python 3.3+"
    else
        print_warning "Cannot automatically install python3-venv"
        print_message "Please install it manually for your distribution"
        exit 1
    fi
    
    print_success "python3-venv installed"
}

# Create virtual environment
create_virtualenv() {
    print_message "Creating Python virtual environment..."
    
    if [[ -d "$VENV_DIR" ]]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf "$VENV_DIR"
    fi
    
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    if [[ -d "$VENV_DIR" ]]; then
        print_success "Virtual environment created at: $VENV_DIR"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
}

# Install Python requirements
install_python_requirements() {
    print_message "Installing Python requirements..."
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r "$REQUIREMENTS_FILE"
    
    # Install additional packages if needed
    pip install PyQt5 qtawesome opencv-python
    
    print_success "Python requirements installed"
}

# Check for FFmpeg
check_ffmpeg() {
    print_message "Checking for FFmpeg..."
    
    if command -v ffmpeg &>/dev/null && command -v ffprobe &>/dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
        print_success "FFmpeg found: $FFMPEG_VERSION"
    else
        print_warning "FFmpeg is not installed. Video processing will not work!"
        print_message "Please install FFmpeg:"
        echo "  Ubuntu/Debian: sudo apt install ffmpeg"
        echo "  Fedora: sudo dnf install ffmpeg"
        echo "  Arch: sudo pacman -S ffmpeg"
        echo "  macOS: brew install ffmpeg"
        echo ""
        print_message "You can continue installation and install FFmpeg later."
    fi
}

# Create start script
create_start_script() {
    print_message "Creating start script..."
    
    cat > "$START_SCRIPT" << 'EOF'
#!/bin/bash
# NamaCut Start Script
# Activates virtual environment and starts the application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
MAIN_PY="$SCRIPT_DIR/main.py"

# Change to script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Error: Virtual environment not found!"
    echo "Please run install.sh first to install NamaCut."
    exit 1
fi

# Activate virtual environment
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Error: Cannot activate virtual environment"
    exit 1
fi

# Run the application
exec python3 "$MAIN_PY" "$@"
EOF
    
    chmod +x "$START_SCRIPT"
    print_success "Start script created: $START_SCRIPT"
}

# Create MIME type file for video files
create_mime_file() {
    print_message "Creating MIME type association..."
    
    cat > "$MIME_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="video/mp4">
    <comment>MP4 video</comment>
    <glob pattern="*.mp4"/>
    <glob pattern="*.m4v"/>
    <glob pattern="*.mp4v"/>
  </mime-type>
  <mime-type type="video/x-msvideo">
    <comment>AVI video</comment>
    <glob pattern="*.avi"/>
  </mime-type>
  <mime-type type="video/quicktime">
    <comment>QuickTime video</comment>
    <glob pattern="*.mov"/>
    <glob pattern="*.qt"/>
  </mime-type>
  <mime-type type="video/x-matroska">
    <comment>Matroska video</comment>
    <glob pattern="*.mkv"/>
    <glob pattern="*.mks"/>
    <glob pattern="*.mk3d"/>
  </mime-type>
  <mime-type type="video/x-ms-wmv">
    <comment>Windows Media video</comment>
    <glob pattern="*.wmv"/>
  </mime-type>
  <mime-type type="video/webm">
    <comment>WebM video</comment>
    <glob pattern="*.webm"/>
  </mime-type>
  <mime-type type="video/x-flv">
    <comment>Flash video</comment>
    <glob pattern="*.flv"/>
  </mime-type>
  <mime-type type="video/mpeg">
    <comment>MPEG video</comment>
    <glob pattern="*.mpeg"/>
    <glob pattern="*.mpg"/>
    <glob pattern="*.mpe"/>
  </mime-type>
  <mime-type type="video/3gpp">
    <comment>3GPP video</comment>
    <glob pattern="*.3gp"/>
    <glob pattern="*.3g2"/>
  </mime-type>
  <mime-type type="video/ogg">
    <comment>Ogg video</comment>
    <glob pattern="*.ogv"/>
    <glob pattern="*.ogg"/>
  </mime-type>
</mime-info>
EOF
    
    # Install MIME type
    if [[ -w "/usr/share/mime/packages" ]]; then
        sudo cp "$MIME_FILE" "/usr/share/mime/packages/"
        print_success "MIME types installed system-wide"
    else
        mkdir -p "$HOME/.local/share/mime/packages"
        cp "$MIME_FILE" "$HOME/.local/share/mime/packages/"
        print_success "MIME types installed for user"
    fi
    
    # Update MIME database
    if command -v update-mime-database &>/dev/null; then
        if [[ -w "/usr/share/mime" ]]; then
            sudo update-mime-database /usr/share/mime
        else
            update-mime-database "$HOME/.local/share/mime"
        fi
        print_success "MIME database updated"
    fi
}

# Create desktop file with MIME associations
create_desktop_file() {
    print_message "Creating desktop entry with file associations..."
    
    # Check if icon exists
    if [[ ! -f "$ICON_FILE" ]]; then
        print_warning "Icon file not found: $ICON_FILE"
        print_warning "Will use system default icon"
        ICON_PATH="video-display"
    else
        ICON_PATH="$SCRIPT_DIR/$ICON_FILE"
    fi
    
    # Create desktop file content with MIME types
    DESKTOP_CONTENT="[Desktop Entry]
Type=Application
Version=1.0
Name=$APP_NAME
GenericName=Video Editor
Comment=Video Cutter and Editor
Exec=$SCRIPT_DIR/$START_SCRIPT %F
Path=$SCRIPT_DIR
Icon=$ICON_PATH
Terminal=false
Categories=AudioVideo;Video;AudioVideoEditing;
Keywords=video;editor;cutter;ffmpeg;
StartupNotify=true
StartupWMClass=namacut
MimeType=video/mp4;video/x-msvideo;video/quicktime;video/x-matroska;video/x-ms-wmv;video/webm;video/x-flv;video/mpeg;video/3gpp;video/ogg;
Actions=Open;

[Desktop Action Open]
Name=Open with $APP_NAME
Exec=$SCRIPT_DIR/$START_SCRIPT %F
Icon=$ICON_PATH"

    # Try to install system-wide first, then user-specific
    if [[ -w "/usr/share/applications" ]]; then
        DESKTOP_PATH="/usr/share/applications/$DESKTOP_FILE"
        echo "$DESKTOP_CONTENT" | sudo tee "$DESKTOP_PATH" > /dev/null
        sudo chmod +x "$DESKTOP_PATH"
        print_success "Desktop entry created system-wide: $DESKTOP_PATH"
    else
        USER_APPS_DIR="$HOME/.local/share/applications"
        mkdir -p "$USER_APPS_DIR"
        DESKTOP_PATH="$USER_APPS_DIR/$DESKTOP_FILE"
        echo "$DESKTOP_CONTENT" > "$DESKTOP_PATH"
        chmod +x "$DESKTOP_PATH"
        print_success "Desktop entry created for user: $DESKTOP_PATH"
    fi
    
    # Update desktop database
    if command -v update-desktop-database &>/dev/null; then
        if [[ "$DESKTOP_PATH" == /usr/share/applications/* ]]; then
            sudo update-desktop-database
        else
            update-desktop-database "$USER_APPS_DIR"
        fi
        print_success "Desktop database updated"
    fi
    
    # Create desktop shortcut (optional)
    print_message "Create desktop shortcut? (Y/n)"
    read -r response
    if [[ ! "$response" =~ ^([nN][oO]|[nN])$ ]]; then
        cp "$DESKTOP_PATH" "$HOME/Desktop/$DESKTOP_FILE"
        chmod +x "$HOME/Desktop/$DESKTOP_FILE"
        print_success "Desktop shortcut created"
    fi
}

# Set as default application for video files
set_as_default() {
    print_message "Would you like to set NamaCut as default application for video files? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        return
    fi
    
    if command -v xdg-mime &>/dev/null; then
        # Set for common video formats
        VIDEO_MIMES=(
            "video/mp4"
            "video/x-msvideo"
            "video/quicktime"
            "video/x-matroska"
            "video/x-ms-wmv"
            "video/webm"
            "video/x-flv"
            "video/mpeg"
            "video/3gpp"
            "video/ogg"
        )
        
        for mime in "${VIDEO_MIMES[@]}"; do
            xdg-mime default "$DESKTOP_FILE" "$mime" 2>/dev/null || true
        done
        
        print_success "NamaCut set as default application for video files"
        print_message "You may need to log out and log back in for changes to take effect"
    else
        print_warning "xdg-mime not found. Cannot set as default application."
    fi
}

# Add context menu entry for Nautilus (GNOME Files)
add_nautilus_script() {
    print_message "Adding 'Open with NamaCut' to right-click menu..."
    
    # Create script for Nautilus
    NAUTILUS_SCRIPT_DIR="$HOME/.local/share/nautilus/scripts"
    NAUTILUS_SCRIPT="$NAUTILUS_SCRIPT_DIR/Open with NamaCut"
    
    mkdir -p "$NAUTILUS_SCRIPT_DIR"
    
    cat > "$NAUTILUS_SCRIPT" << 'EOF'
#!/bin/bash
# Nautilus script to open video files with NamaCut

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")/../../.."
START_SCRIPT="$SCRIPT_DIR/start.sh"

# Get selected files
for video_file in "$@"; do
    if [ -f "$video_file" ]; then
        "$START_SCRIPT" "$video_file" &
    fi
done
EOF
    
    chmod +x "$NAUTILUS_SCRIPT"
    print_success "Nautilus script created"
}

# Add context menu entry for Dolphin (KDE)
add_dolphin_service() {
    print_message "Adding service menu for Dolphin..."
    
    DOLPHIN_SERVICE_DIR="$HOME/.local/share/kservices5"
    DOLPHIN_SERVICE_FILE="$DOLPHIN_SERVICE_DIR/ServiceMenus/namacut.desktop"
    
    mkdir -p "$(dirname "$DOLPHIN_SERVICE_FILE")"
    
    cat > "$DOLPHIN_SERVICE_FILE" << EOF
[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=video/mp4;video/x-msvideo;video/quicktime;video/x-matroska;video/x-ms-wmv;video/webm;video/x-flv;video/mpeg;video/3gpp;video/ogg
Actions=OpenWithNamaCut
Icon=$SCRIPT_DIR/$ICON_FILE

[Desktop Action OpenWithNamaCut]
Name=Open with NamaCut
Exec=$SCRIPT_DIR/$START_SCRIPT %F
Icon=$SCRIPT_DIR/$ICON_FILE
EOF
    
    print_success "Dolphin service menu created"
}

# Add context menu entry for Thunar (XFCE)
add_thunar_action() {
    print_message "Adding action for Thunar..."
    
    THUNAR_ACTION_DIR="$HOME/.config/Thunar"
    THUNAR_UCA_FILE="$THUNAR_ACTION_DIR/uca.xml"
    
    # Create directory if it doesn't exist
    mkdir -p "$THUNAR_ACTION_DIR"
    
    # Check if uca.xml exists
    if [[ ! -f "$THUNAR_UCA_FILE" ]]; then
        cat > "$THUNAR_UCA_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<actions>
</actions>
EOF
    fi
    
    # Define the new action
    NEW_ACTION=$(cat << 'EOF'
<action>
  <icon>video-display</icon>
  <name>Open with NamaCut</name>
  <unique-id>1671218075276718-1</unique-id>
  <command>$SCRIPT_DIR/start.sh %F</command>
  <description>Open video file with NamaCut Video Editor</description>
  <patterns>*</patterns>
  <video-files/>
  <audio-files/>
</action>
EOF
)
    
    # Temporarily replace SCRIPT_DIR
    NEW_ACTION="${NEW_ACTION//\$SCRIPT_DIR/$SCRIPT_DIR}"
    
    # Add to uca.xml
    if grep -q "Open with NamaCut" "$THUNAR_UCA_FILE"; then
        print_warning "Thunar action already exists"
    else
        # Insert before closing </actions> tag
        sed -i 's|</actions>|'"$NEW_ACTION"'</actions>|' "$THUNAR_UCA_FILE"
        print_success "Thunar action added"
    fi
}

# Fix permissions
fix_permissions() {
    print_message "Setting up permissions..."
    
    # Make Python files executable
    chmod +x "$MAIN_PY"
    
    # Make sure start script is executable
    chmod +x "$START_SCRIPT"
    
    print_success "Permissions set"
}

# Main installation function
main_install() {
    echo "========================================"
    echo "    NamaCut Video Editor Installation"
    echo "========================================"
    echo ""
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. It's better to run as regular user."
        print_message "Continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            exit 1
        fi
    fi
    
    # Run installation steps
    check_python
    install_python_venv
    create_virtualenv
    install_python_requirements
    check_ffmpeg
    create_start_script
    create_mime_file
    
    # Ask about desktop entry
    echo ""
    print_message "Create desktop menu entry? (Y/n)"
    read -r response
    if [[ ! "$response" =~ ^([nN][oO]|[nN])$ ]]; then
        create_desktop_file
    fi
    
    # Ask about file associations
    echo ""
    print_message "Add 'Open with NamaCut' to right-click menu? (Y/n)"
    read -r response
    if [[ ! "$response" =~ ^([nN][oO]|[nN])$ ]]; then
        # Detect desktop environment
        if [[ "$XDG_CURRENT_DESKTOP" =~ "GNOME" ]] || [[ "$GDMSESSION" =~ "gnome" ]]; then
            add_nautilus_script
        elif [[ "$XDG_CURRENT_DESKTOP" =~ "KDE" ]] || [[ "$GDMSESSION" =~ "plasma" ]]; then
            add_dolphin_service
        elif [[ "$XDG_CURRENT_DESKTOP" =~ "XFCE" ]] || [[ "$GDMSESSION" =~ "xfce" ]]; then
            add_thunar_action
        else
            print_warning "Unknown desktop environment. Trying to add for all..."
            add_nautilus_script
            add_dolphin_service
            add_thunar_action
        fi
    fi
    
    # Ask about setting as default
    echo ""
    set_as_default
    
    fix_permissions
    
    echo ""
    echo "========================================"
    print_success "Installation completed successfully!"
    echo ""
    echo "Features installed:"
    echo "✓ Python virtual environment"
    echo "✓ All dependencies"
    echo "✓ Desktop menu entry"
    echo "✓ File associations for video files"
    echo "✓ 'Open with NamaCut' in right-click menu"
    echo ""
    echo "You can now:"
    echo "1. Find 'NamaCut' in your application menu"
    echo "2. Right-click on video files → 'Open with NamaCut'"
    echo "3. Double-click video files (if set as default)"
    echo "4. Run from terminal: ./start.sh"
    echo ""
    echo "Note: You may need to log out and log back in for all"
    echo "      context menu changes to take effect."
    echo "========================================"
}

# Run main installation
main_install
