from flask import Flask, render_template, request, jsonify
from flask_httpauth import HTTPBasicAuth
import json
import os
import math
from datetime import datetime
from pywebpush import webpush, WebPushException

app = Flask(__name__)
auth = HTTPBasicAuth()

# --- Security ---
# IMPORTANT: Change this username and password.
# For better security, use environment variables instead of hardcoding.
# For example: USERS = {os.environ.get('APP_USERNAME'): os.environ.get('APP_PASSWORD')}
USERS = {
    "admin": "secret"
}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS[username] == password:
        return username

# --- Endpoints ---

# File to store thoughts
THOUGHTS_FILE = 'thoughts.json'
VAPID_KEYS_FILE = 'vapid_keys.json'
SUBSCRIPTION_FILE = 'subscription.json'

def get_thoughts():
    if not os.path.exists(THOUGHTS_FILE):
        return []
    with open(THOUGHTS_FILE, 'r') as f:
        return json.load(f)

def save_thoughts(thoughts):
    with open(THOUGHTS_FILE, 'w') as f:
        json.dump(thoughts, f, indent=4)

def get_subscription():
    if not os.path.exists(SUBSCRIPTION_FILE):
        return None
    with open(SUBSCRIPTION_FILE, 'r') as f:
        return json.load(f)

def save_subscription(subscription):
    with open(SUBSCRIPTION_FILE, 'w') as f:
        json.dump(subscription, f, indent=4)

def get_vapid_keys():
    with open(VAPID_KEYS_FILE, 'r') as f:
        return json.load(f)

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/vapid_public_key', methods=['GET'])
@auth.login_required
def vapid_public_key():
    keys = get_vapid_keys()
    return jsonify({'public_key': keys['public_key_b64']})

@app.route('/subscription', methods=['POST'])
@auth.login_required
def subscription():
    subscription = request.json
    save_subscription(subscription)
    return jsonify({'status': 'ok'})

import math

# ... (previous imports)

# --- Endpoints ---
PAGE_SIZE = 10
# ... (rest of the file before list_thoughts)

@app.route('/thoughts', methods=['GET'])
@auth.login_required
def list_thoughts():
    page = request.args.get('page', 1, type=int)
    all_thoughts = get_thoughts()
    
    total_thoughts = len(all_thoughts)
    total_pages = math.ceil(total_thoughts / PAGE_SIZE)
    
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    paginated_thoughts = all_thoughts[start:end]
    
    return jsonify({
        'thoughts': paginated_thoughts,
        'page': page,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    })

@app.route('/thoughts', methods=['POST'])
@auth.login_required
def add_thought():
    thought = request.json.get('thought')
    if thought:
        thoughts = get_thoughts()
        new_thought = {
            'text': thought,
            'timestamp': datetime.utcnow().isoformat()
        }
        thoughts.insert(0, new_thought)
        save_thoughts(thoughts)

        subscription = get_subscription()
        if subscription:
            try:
                vapid_keys = get_vapid_keys()
                webpush(
                    subscription_info=subscription,
                    data=json.dumps({'title': 'New Thought!', 'body': thought}),
                    vapid_private_key=vapid_keys['private_key'],
                    vapid_claims={
                        'sub': 'mailto:your_email@example.com'
                    }
                )
            except WebPushException as ex:
                print(f"Web push failed: {ex}")

        return jsonify({'status': 'ok'}), 201
    return jsonify({'error': 'Invalid thought'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
