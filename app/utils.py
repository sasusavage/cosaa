import os
import requests
import random
import string
import threading
from datetime import datetime, timedelta

def format_gh_number(number):
    """Formats a Ghanaian number to the 233XXXXXXXXX format."""
    num = ''.join(filter(str.isdigit, str(number)))
    if num.startswith('0') and len(num) == 10:
        return '233' + num[1:]
    if len(num) == 9:
        return '233' + num
    return num

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
    
    # Ensure recipients is a list and formatted for Ghana (233)
    if isinstance(recipients, str):
        recipients = [recipients]
    
    formatted_recipients = [format_gh_number(r) for r in recipients]
        
    payload = {
        "message": message,
        "recipients": formatted_recipients,
        "sender": sender
    }
    
    try:
        print(f"Attempting to send SMS to {formatted_recipients} via Vynfy...")
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        print(f"Vynfy Gateway Response: {res_data}")
        
        if res_data.get('success'):
            return res_data
        else:
            print(f"Vynfy API Error: {res_data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Network/Internal Error sending SMS: {e}")
        return None

def send_sms_async(recipients, message):
    """
    Sends SMS in a background thread so the user doesn't have to wait 
    for the API response.
    """
    thread = threading.Thread(target=send_sms, args=(recipients, message))
    thread.start()
    return True

def generate_otp(length=6):
    """Generates a numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))
