import json
import os
import math
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename
from pywebpush import webpush, WebPushException
from PIL import Image

# --- App and Auth Initialization ---
app = Flask(__name__)
auth = HTTPBasicAuth()

# --- Constants ---
THOUGHTS_FILE = 'thoughts.json'
VAPID_KEYS_FILE = 'vapid_keys.json'
SUBSCRIPTION_FILE = 'subscription.json'
PAGE_SIZE = 10

# --- Security ---
# IMPORTANT: Change this username and password.
# For better security, use environment variables.
USERS = {
    "admin": "secret"
}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS.get(username) == password:
        return username
    return None

# --- Helper Functions ---
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

# --- Core Routes ---
@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/thoughts', methods=['GET'])
@auth.login_required
def list_thoughts():
    page = request.args.get('page', 1, type=int)
    all_thoughts = get_thoughts()
    
    total_thoughts = len(all_thoughts)
    total_pages = math.ceil(total_thoughts / PAGE_SIZE) if total_thoughts > 0 else 1
    
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
    thought_text = request.json.get('thought')
    if thought_text:
        thoughts = get_thoughts()
        new_thought = {
            'text': thought_text,
            'timestamp': datetime.utcnow().isoformat() + 'Z' # Add Z for UTC
        }
        thoughts.insert(0, new_thought)
        save_thoughts(thoughts)

        # Send push notification
        subscription = get_subscription()
        if subscription:
            try:
                vapid_keys = get_vapid_keys()
                webpush(
                    subscription_info=subscription,
                    data=json.dumps({'title': 'New Thought!', 'body': thought_text}),
                    vapid_private_key=vapid_keys['private_key'],
                    vapid_claims={'sub': 'mailto:your_email@example.com'}
                )
            except WebPushException as ex:
                print(f"Web push failed: {ex}")

        return jsonify({'status': 'ok'}), 201
    return jsonify({'error': 'Invalid thought'}), 400

# --- Upload and Subscription Routes ---
@app.route('/upload_image', methods=['POST'])
@auth.login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Check for allowed extensions before processing
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in file.filename or file.filename.split('.')[-1].lower() not in allowed_extensions:
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Open the image from the stream
        img = Image.open(file.stream)

        # Set a max width and calculate the new height to maintain aspect ratio
        max_width = 1024
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # As requested, convert to PNG. Note: For photos, this may increase file size.
        # Saving as JPEG with quality settings might be a better option for photos.
        
        # Generate a unique filename with a .png extension
        filename = f"{uuid.uuid4()}.png"
        upload_path = os.path.join('static', 'uploads', filename)
        
        # Save the optimized image
        img.save(upload_path, 'PNG')
        
        return jsonify({'url': f'/{upload_path}'})

    except Exception as e:
        return jsonify({'error': f"Error processing image: {e}"}), 500

@app.route('/vapid_public_key', methods=['GET'])
@auth.login_required
def vapid_public_key():
    keys = get_vapid_keys()
    return jsonify({'public_key': keys['public_key_b64']})

@app.route('/subscription', methods=['POST'])
@auth.login_required
def subscription():
    subscription_data = request.json
    save_subscription(subscription_data)
    return jsonify({'status': 'ok'})

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)