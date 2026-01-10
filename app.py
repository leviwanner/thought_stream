import json
import os
import math
import uuid
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from pywebpush import webpush, WebPushException
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- App and Auth Initialization ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-please-change')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to /login if user is not authenticated

# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        # In a real app, this would query a database
        stored_username = os.environ.get("APP_USERNAME", "admin")
        stored_password = os.environ.get("APP_PASSWORD", "secret")
        
        # We only have one user, so if the ID is 1, we return that user
        if user_id == '1':
            # For simplicity, we are hashing the password on every get request.
            # In a real app, this hash would be stored.
            password_hash = generate_password_hash(stored_password)
            return User(id='1', username=stored_username, password_hash=password_hash)
        return None

    @staticmethod
    def get_by_username(username):
        stored_username = os.environ.get("APP_USERNAME", "admin")
        if username == stored_username:
            return User.get('1')
        return None

# Flask-Login requires this function to load a user from the session
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# --- Constants ---
THOUGHTS_FILE = 'thoughts.json'
SUBSCRIPTION_FILE = 'subscription.json'
PAGE_SIZE = 10

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

# --- Login/Logout Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Core Routes ---
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/thoughts', methods=['GET'])
@login_required
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
@login_required
def add_thought():
    thought_text = request.json.get('thought')
    if thought_text:
        thoughts = get_thoughts()
        new_thought = {
            'text': thought_text,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        thoughts.insert(0, new_thought)
        save_thoughts(thoughts)
        # Notification on new thought has been disabled as per user request.
        return jsonify({'status': 'ok'}), 201
    return jsonify({'error': 'Invalid thought'}), 400

# --- Upload and Subscription Routes ---
@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        img = Image.open(file.stream)
        max_width = 1024
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        filename = f"{uuid.uuid4()}.png"
        upload_path = os.path.join('static', 'uploads', filename)
        img.save(upload_path, 'PNG')
        return jsonify({'url': f'/{upload_path}'})
    except Exception as e:
        return jsonify({'error': f"Error processing image: {e}"}), 500

@app.route('/vapid_public_key', methods=['GET'])
@login_required
def vapid_public_key():
    with open('vapid_public.txt', 'r') as f:
        public_key = f.read().strip()
    return jsonify({'public_key': public_key})

@app.route('/subscription', methods=['POST'])
@login_required
def subscription():
    subscription_data = request.json
    save_subscription(subscription_data)
    return jsonify({'status': 'ok'})

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
