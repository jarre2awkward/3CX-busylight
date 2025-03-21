#!/bin/bash

set -e

echo "📦 Starting 3CX Busylight Setup..."

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv ~/3CX-licht/busylight-venv
source ~/3CX-licht/busylight-venv/bin/activate

# Upgrade pip and install requirements
echo "⬆️ Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -r ~/3CX-busylight/requirements.txt

# Create logs folder
echo "📝 Creating log folder..."
mkdir -p /home/$USER/logs
touch /home/$USER/logs/cronlog
chmod -R 777 /home/$USER/logs

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
sudo cp ~/3CX-licht/busylight.service /etc/systemd/system/busylight.service
sudo systemctl daemon-reload
sudo systemctl enable busylight.service
sudo systemctl start busylight.service

echo "✅ Setup complete. Busylight should now run in the background."

