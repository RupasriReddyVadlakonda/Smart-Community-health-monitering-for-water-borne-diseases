from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Read Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
MY_MOBILE_NUMBER = os.getenv("MY_MOBILE_NUMBER")

# Check that all variables are loaded
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, MY_MOBILE_NUMBER]):
    raise ValueError("One or more Twilio environment variables are missing!")

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


try:
    message = client.messages.create(
        body="Test SMS from Water Disease Predictor",
        from_=TWILIO_PHONE_NUMBER,
        to=MY_MOBILE_NUMBER
    )
    print("✅ SMS sent successfully! SID:", message.sid)
except Exception as e:
    print("❌ SMS failed:", e)
