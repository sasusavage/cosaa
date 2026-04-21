import os
import requests
import random
import string
from datetime import datetime, timedelta

def send_sms(recipients, message):
    """
    Sends an SMS using the Vynfy API.
    recipients: string or list of strings
    message: string (max 650 chars)
    """
    api_key = os.environ.get('VYNFY_API_KEY')
    sender = os.environ.get('VYNFY_SENDER_ID', 'CoSSA')
    url = "https://sms.vynfy.com/api/v1/send"
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Ensure recipients is a list
    if isinstance(recipients, str):
        recipients = [recipients]
        
    payload = {
        "message": message,
        "recipients": recipients,
        "sender": sender
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return None

def generate_otp(length=6):
    """Generates a numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))
