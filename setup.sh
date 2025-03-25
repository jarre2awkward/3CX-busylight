#!/bin/bash

set -e

echo "📦 Starting 3CX Busylight Setup..."

# Ask for extensions and PBX domain
read -p "📞 Enter the extension numbers to monitor (comma-separated, e.g. 201,202,203): " extensions_input
read -p "🌐 Enter the PBX monitor domain (e.g. https://pdss.3cx.eu): " pbx_domain

# Replace placeholders in licht.py
sed -i "s|EXTENSIONS_TO_MONITOR = .*|EXTENSIONS_TO_MONITOR = [$(echo $extensions_input | sed 's/,/\", \"/g; s/^/\"/; s/$/\"]/')|" /home/PDSS/3CX-busylight/licht.py
sed -i "s|API_URL = .*|API_URL = \"$pbx_domain/connect/token\"|" /home/PDSS/3CX-busylight/licht.py

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv /home/PDSS/3CX-licht/busylight-venv
source /home/PDSS/3CX-licht/busylight-venv/bin/activate

# Upgrade pip and install requirements
echo "⬆️ Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -r /home/PDSS/3CX-busylight/requirements.txt

# Create logs folder
echo "📝 Creating log folder..."
mkdir -p /home/PDSS/logs
touch /home/PDSS/logs/cronlog
chmod -R 777 /home/PDSS/logs

# ✅ Show USB Devices
echo "🔌 Connected USB devices:"
lsusb
echo ""
read -p "🔍 Enter the line number of the Busylight device (starting from 1): " line_number

# ✅ Extract Vendor ID and Product ID
usb_line=$(lsusb | sed -n "${line_number}p")
vendor_id=$(echo "$usb_line" | awk '{print $6}' | cut -d: -f1)
product_id=$(echo "$usb_line" | awk '{print $6}' | cut -d: -f2)

echo "✅ Detected Vendor ID: $vendor_id, Product ID: $product_id"

# ✅ Create udev rule
echo "🛠 Adding udev rule for Busylight..."
echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"$vendor_id\", ATTRS{idProduct}==\"$product_id\", MODE=\"666\"" | sudo tee /etc/udev/rules.d/99-busylight.rules > /dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger

# ✅ Install systemd service
echo "🔧 Installing and enabling systemd service..."
sudo cp /home/PDSS/3CX-busylight/busylight.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable busylight.service
sudo systemctl start busylight.service

echo "✅ Setup complete. Busylight should now run in the background."
