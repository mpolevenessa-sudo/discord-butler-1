import requests

# This is your local FastAPI server address
WEBHOOK_URL = "http://127.0.0.1:8000/whop/webhook"

# Faking the data that Whop sends when a credit card declines
payload = {
    "action": "payment_failed",
    "discord_id": "1169672054941958265"  # <--- PUT YOUR ID HERE!
}

print("Sending fake Whop Webhook...")
try:
    response = requests.post(WEBHOOK_URL, json=payload)
    print(f"Server Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")