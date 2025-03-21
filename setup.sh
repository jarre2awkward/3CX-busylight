#!/bin/bash
set -e

echo "📦 Busylight installatie gestart..."

mkdir -p ~/3CX-licht
python3 -m venv ~/3CX-licht/busylight-venv
source ~/3CX-licht/busylight-venv/bin/activate

echo "⬆️ Pip en requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📁 Log directory maken..."
mkdir -p /home/pi/logs
touch /home/pi/logs/cronlog
chmod -R 777 /home/pi/logs

echo "🔌 USB devices aangesloten:"
lsusb
echo ""
read -p "👉 Nummer van de Busylight regel in lsusb (bv. 2): " lineno

usb_line=$(lsusb | sed -n "${lineno}p")
vendor_id=$(echo "$usb_line" | awk '{print $6}' | cut -d: -f1)
product_id=$(echo "$usb_line" | awk '{print $6}' | cut -d: -f2)

echo "🛠 Voeg udev rule toe..."
echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"$vendor_id\", ATTRS{idProduct}==\"$product_id\", MODE=\"666\"" | sudo tee /etc/udev/rules.d/99-busylight.rules > /dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "🧠 Kopieer licht.py naar juiste locatie..."
sudo cp licht.py /usr/local/bin/licht.py
sudo chmod +x /usr/local/bin/licht.py

echo "🔧 Systemd service installeren..."
sudo cp busylight.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable busylight.service
sudo systemctl start busylight.service

echo "✅ Setup voltooid! Busylight draait nu op de achtergrond."
