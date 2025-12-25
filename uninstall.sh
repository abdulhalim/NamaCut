#!/bin/bash
# NamaCut Uninstall Script

set -e

APP_NAME="NamaCut"
VENV_DIR="venv"
DESKTOP_FILE="namacut.desktop"
START_SCRIPT="start.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "========================================"
echo "    NamaCut Uninstallation"
echo "========================================"
echo ""

# Confirm uninstall
read -p "Are you sure you want to uninstall $APP_NAME? (y/N): " confirm
if [[ ! "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove virtual environment
if [[ -d "$VENV_DIR" ]]; then
    echo "Removing virtual environment..."
    rm -rf "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment removed${NC}"
fi

# Remove start script
if [[ -f "$START_SCRIPT" ]]; then
    echo "Removing start script..."
    rm -f "$START_SCRIPT"
    echo -e "${GREEN}✓ Start script removed${NC}"
fi

# Remove desktop entries
echo "Removing desktop entries..."
rm -f "$HOME/.local/share/applications/$DESKTOP_FILE"
rm -f "/usr/share/applications/$DESKTOP_FILE"
rm -f "$HOME/Desktop/$DESKTOP_FILE"

# Update desktop database
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    sudo update-desktop-database 2>/dev/null || true
fi

echo -e "${GREEN}✓ Desktop entries removed${NC}"
echo ""
echo "========================================"
echo "    Uninstallation complete!"
echo "========================================"
echo ""
echo "Note: Your video files and settings are preserved."
echo "To completely remove, delete the NamaCut folder."
