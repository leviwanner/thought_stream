import json
import os
import sys
import base64
from dotenv import load_dotenv
from pywebpush import webpush, WebPushException

# --- Get the absolute path of the script's directory ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = script_dir

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

    if not os.path.exists(SUBSCRIPTION_FILE):
        print(f"Error: Subscription file not found.", file=sys.stderr)
        return
    with open(SUBSCRIPTION_FILE, 'r') as f:
        subscription_info = json.load(f)
    print("Loaded subscription info.")

    if not os.path.exists(VAPID_KEYS_FILE):
        print(f"Error: VAPID keys file not found.", file=sys.stderr)
        return
    with open(VAPID_KEYS_FILE, 'r') as f:
        vapid_keys = json.load(f)
    print("Loaded VAPID keys.")

    vapid_claims = {
        'sub': os.environ.get('VAPID_CLAIMS_EMAIL', 'mailto:your-email@example.com')
    }
    print(f"Using VAPID claims: {vapid_claims}")

    try:
        # Decode the base64 private key before using it
        private_key_bytes = base64.b64decode(vapid_keys['private_key'])

        webpush(
            subscription_info=subscription_info,
            data=PUSH_DATA.encode('utf-8'),
            vapid_private_key=private_key_bytes,
            vapid_claims=vapid_claims
        )
        print("Successfully sent the push notification.")
    except WebPushException as ex:
        print(f"Web push failed: {ex}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == '__main__':
    send_prompt()