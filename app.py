berfrom flask import Flask, request
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime
import re
import urllib3

app = Flask(__name__)

# Disable SSL warnings (only for local testing)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== Google Sheets Configuration ====
SERVICE_ACCOUNT_FILE = r"C:\Users\admin\PycharmProjects\pythonProject1\LearnXpert\credentials.json"
SPREADSHEET_ID = "1aUXIvQrx5ddsJwDZ0dfXniN47KUaFArJizHUFzdks4E"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=creds)
sheet = sheet_service.spreadsheets()

# ==== Maytapi Configuration ====
PRODUCT_ID = "95c07265-ac4b-41ea-8c22-794f3ac39044"   # Replace with your Product ID
PHONE_ID = "119070"                                   # Replace with your Phone ID
API_TOKEN = "abadf380-7d8d-470a-9f1f-2163388c4c7c"                  # Replace with your Maytapi token
MAYTAPI_URL = f"https://api.maytapi.com/api/{PRODUCT_ID}/{PHONE_ID}/sendMessage"

# ==== Helper Function to Send WhatsApp Message ====
def send_whatsapp_message(phone, message):
    try:
        payload = {
            "to_number": phone,
            "type": "text",
            "message": message
        }
        headers = {
            "Content-Type": "application/json",
            "x-maytapi-key": API_TOKEN
        }
        response = requests.post(MAYTAPI_URL, json=payload, headers=headers, verify=False)
        print(f"✅ Sent message to {phone}: {message}")
        print(f"📨 Maytapi Response: {response.text}")
    except Exception as e:
        print("❌ Error sending message:", e)

# ==== WhatsApp Webhook ====
@app.route('/vnr_whatsapp_incoming', methods=['POST'])
def whatsapp_webhook():
    try:
        data = request.json
        print("📩 Incoming Webhook Data:", data)

        # Parse message details
        message = data.get("message", {}).get("text", "").strip()
        phone = data.get("user", {}).get("phone", "")

        if not phone or not message:
            return "No valid message", 400

        # Log to Google Sheets
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = [[phone, message, now]]
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A:C",
            valueInputOption="USER_ENTERED",
            body={"values": values}
        ).execute()

        # ==== Reply Logic ====
        reply = None

        # Menu options
        if message.lower() in ["hi", "hello", "menu", "start"]:
            reply = (
                "🌿 *Welcome to VNR Milk Hub!* 🌿\n"
                "Please choose an option below:\n\n"
                "1️⃣ View Product List\n"
                "2️⃣ Place an Order\n"
                "3️⃣ Talk to Support"
            )

        elif message.strip() == "1":
            reply = (
                "🥛 *Our Products:*\n"
                "• Organic Cow Milk\n"
                "• Buffalo Milk\n"
                "• Ghee\n"
                "• Paneer\n"
                "• Curd\n\n"
                "Reply *2* to order now!"
            )

        elif message.strip() == "2":
            reply = (
                "🛒 Please type your order in this format:\n"
                "*Name - Product - Quantity*\n\n"
                "Example: *Zameer - Ghee - 2L*"
            )

        elif re.match(r"^[A-Za-z\s]+-\s*[A-Za-z\s]+-\s*\d+", message):
            reply = (
                "✅ *Order Received!*\n"
                "Thank you for your order. Please share your location 📍 "
                "to confirm delivery."
            )

        elif "location" in message.lower():
            reply = (
                "📍 Thank you! Your location has been noted. "
                "Our team member will deliver your order soon 🚚"
            )

        elif message.strip() == "3":
            reply = "📞 Our support team will contact you shortly."

        else:
            reply = "🙏 Please type *Hi* to start again or choose an option."

        # Send WhatsApp reply
        send_whatsapp_message(phone, reply)

        return "OK", 200

    except Exception as e:
        print("❌ Error:", e)
        return "Error", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

