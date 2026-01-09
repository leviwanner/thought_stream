import json
import os
import sys
from dotenv import load_dotenv
from pywebpush import webpush, WebPushException

# --- Get the absolute path of the script's directory ---
# This is crucial for cron jobs to find the files correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = script_dir  # In this case, the script is in the root

# Load environment variables from .env file in the project root
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Configuration ---
VAPID_KEYS_FILE = os.path.join(project_root, 'vapid_keys.json')
SUBSCRIPTION_FILE = os.path.join(project_root, 'subscription.json')

# Notification content
PUSH_DATA = json.dumps({
    'title': 'Thought Stream',
    'body': "What's on your mind?"
})

def send_prompt():
    """
    Sends a push notification prompt to the subscribed user.
    """
    print("Attempting to send push notification prompt...")

    # --- Load Subscription ---
    if not os.path.exists(SUBSCRIPTION_FILE):
        print(f"Error: Subscription file not found at '{SUBSCRIPTION_FILE}'. Cannot send prompt.", file=sys.stderr)
        return
    with open(SUBSCRIPTION_FILE, 'r') as f:
        subscription_info = json.load(f)
    print("Loaded subscription info.")

    # --- Load VAPID Keys ---
    if not os.path.exists(VAPID_KEYS_FILE):
        print(f"Error: VAPID keys file not found at '{VAPID_KEYS_FILE}'.", file=sys.stderr)
        return
    with open(VAPID_KEYS_FILE, 'r') as f:
        vapid_keys = json.load(f)
    print("Loaded VAPID keys.")

    # --- Get VAPID Claims from Environment ---
    vapid_claims = {
        'sub': os.environ.get('VAPID_CLAIMS_EMAIL', 'mailto:your-email@example.com')
    }
    print(f"Using VAPID claims: {vapid_claims}")

    # --- Send the Push Notification ---
    try:
        webpush(
            subscription_info=subscription_info,
            data=PUSH_DATA,
            vapid_private_key=vapid_keys['private_key'],
            vapid_claims=vapid_claims
        )
        print("Successfully sent the push notification.")
    except WebPushException as ex:
        print(f"Web push failed: {ex}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == '__main__':
    send_prompt()
