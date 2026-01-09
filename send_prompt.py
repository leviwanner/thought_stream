import json
import os
import sys
from dotenv import load_dotenv
from pywebpush import webpush, WebPushException

# --- Get the absolute path of the script's directory ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = script_dir

# Load environment variables from .env file in the project root
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Configuration ---
PRIVATE_KEY_FILE = os.path.join(project_root, 'vapid_private.pem')
SUBSCRIPTION_FILE = os.path.join(project_root, 'subscription.json')

# Notification content
PUSH_DATA = json.dumps({
    'title': 'Thought Reminder',
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

    if not os.path.exists(PRIVATE_KEY_FILE):
        print(f"Error: VAPID private key file not found.", file=sys.stderr)
        return
    print("Found VAPID private key file.")

    vapid_claims = {
        'sub': os.environ.get('VAPID_CLAIMS_EMAIL', 'mailto:your-email@example.com')
    }
    print(f"Using VAPID claims: {vapid_claims}")

    try:
        webpush(
            subscription_info=subscription_info,
            data=PUSH_DATA.encode('utf-8'),
            vapid_private_key=PRIVATE_KEY_FILE, # Pass the file path directly
            vapid_claims=vapid_claims
        )
        print("Successfully sent the push notification.")
    except WebPushException as ex:
        print(f"Web push failed: {ex}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == '__main__':
    send_prompt()
