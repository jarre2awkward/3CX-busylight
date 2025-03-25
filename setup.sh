#!/bin/bash

set -e

echo "📦 Setup starten..."

# Vraag input voor extensies, PBX en API key
read -p "🌐 Geef je PBX domein in (e.g. https://pdss.3cx.eu): " pbx_domain
read -p "📞 Geef de extensienummers die je wilt monitoren in (Afgezonderd per komma, e.g. 201,202,203): " extensions_input
read -p "🔑 Geef je API Key: " api_key

# Pas licht.py aan met opgegeven gegevens
sed -i "s|EXTENSIONS_TO_MONITOR = .*|EXTENSIONS_TO_MONITOR = [$(echo $extensions_input | sed 's/,/\", \"/g; s/^/\"/; s/$/\"]/')]|" /home/PDSS/3CX-busylight/licht.py
sed -i "s|API_URL = .*|API_URL = \"$pbx_domain/connect/token\"|" /home/PDSS/3CX-busylight/licht.py
sed -i "s|CLIENT_SECRET = .*|CLIENT_SECRET = \"$api_key\"|" /home/PDSS/3CX-busylight/licht.py

# Maak virtualenv aan
echo "🐍 Python envirement creëren..."
python3 -m venv /home/PDSS/3CX-licht/busylight-venv
source /home/PDSS/3CX-licht/busylight-venv/bin/activate

# Installeer vereisten
echo "⬆️ pip en dependencies installeren en updaten..."
pip install --upgrade pip
pip install -r /home/PDSS/3CX-busylight/requirements.txt

# Maak logfolder aan
echo "📝 Log folder maken..."
mkdir -p /home/PDSS/logs
touch /home/PDSS/logs/cronlog
chmod -R 777 /home/PDSS/logs

# Toon USB devices en vraag naar keuze
echo "🔌 Verbonden USB-Apparaten:"
lsusb
echo ""
read -p "🔍 Geef de lijnnummer van het lampje in (startend van 1): " line_number

usb_line=$(lsusb | sed -n "${line_number}p")
vendor_id=$(echo "$usb_line" | awk '{print $6}' | cut -d: -f1)
product_id=$(echo "$usb_line" | awk '{print $6}' | cut -d: -f2)

echo "✅ Gevonden Vendor ID: $vendor_id, Product ID: $product_id"

# Voeg udev rule toe
echo "🛠 Udev rule toevoegen voor Busylight..."
echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"$vendor_id\", ATTRS{idProduct}==\"$product_id\", MODE=\"666\"" | sudo tee /etc/udev/rules.d/99-busylight.rules > /dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger

# Kopieer licht.py
sudo cp /home/PDSS/3CX-busylight/licht.py /usr/local/bin/
sudo chmod +x /usr/local/bin/licht.py

# Installeer en start systemd service
echo "🔧 Installeren van systemd service..."
sudo cp /home/PDSS/3CX-busylight/busylight.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable busylight.service
sudo systemctl start busylight.service

echo "✅ Setup voltooid. Het moet gewoon werken."
