# Thought Stream

A simple PWA to share your thoughts.

## Raspberry Pi Setup

These instructions will guide you through setting up and running the Thought Stream application on a Raspberry Pi.

### 1. Prerequisites

*   A Raspberry Pi with Raspberry Pi OS installed.
*   An internet connection.
*   `git` installed (`sudo apt-get install git`).

### 2. Clone the Repository

Clone this repository to your Raspberry Pi:

```bash
git clone <repository_url>
cd thought_stream
```

### 3. Install Dependencies

The application requires Python 3 and some dependencies.

**Install Python 3 and pip:**

```bash
sudo apt-get update
sudo apt-get install python3-venv python3-pip
```

**Create a virtual environment and install the dependencies:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The application uses a `.env` file to manage sensitive configurations like your username, password, and the VAPID claims email for push notifications. This keeps your secrets out of the code and Git repository.

1.  **Create your `.env` file:**
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:**
    ```bash
    nano .env
    ```
    Replace the placeholder values with your desired username, a strong password, and a valid email address (e.g., `mailto:your-email@example.com` or `https://your-website.com`) for the `VAPID_CLAIMS_EMAIL`.

    Example `.env` content:
    ```
    APP_USERNAME=mysecureuser
    APP_PASSWORD=My$uper$ecureP@ssw0rd!
    VAPID_CLAIMS_EMAIL=mailto:my.contact@example.com
    ```
    Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

### 5. Generate VAPID Keys

The application uses VAPID keys for push notifications. You need to generate these keys once.

```bash
python generate_keys.py
```

This will create a `vapid_keys.json` file.

**Important:** Do not share your `vapid_keys.json` file publicly.

### 5. Run the Application

To run the application, execute the following command:

```bash
python app.py
```

The application will be running on `http://<your_pi_ip>:5000`.

### 6. Set up Cloudflare Tunnel

To access your application from the internet, you can use a Cloudflare Tunnel.

1.  **Install `cloudflared` on your Raspberry Pi.**

    Follow the official Cloudflare documentation to install `cloudflared`: [https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)

2.  **Authenticate `cloudflared`:**

    ```bash
    cloudflared tunnel login
    ```

3.  **Create a tunnel:**

    ```bash
    cloudflared tunnel create thought-stream-tunnel
    ```

    This will give you a UUID for your tunnel and create a credentials file.

4.  **Create a configuration file:**

    Create a file named `config.yml` in `/etc/cloudflared/` (you may need to create the directory).

    ```yaml
    tunnel: <your_tunnel_uuid>
    credentials-file: /root/.cloudflared/<your_tunnel_uuid>.json
    ingress:
      - hostname: your-subdomain.your-domain.com
        service: http://localhost:5000
      - service: http_status:404
    ```

    Replace `<your_tunnel_uuid>` with the UUID from the previous step, and `your-subdomain.your-domain.com` with the domain you want to use.

5.  **Route DNS to the tunnel:**

    ```bash
    cloudflared tunnel route dns thought-stream-tunnel your-subdomain.your-domain.com
    ```

6.  **Run the tunnel:**

    ```bash
    cloudflared tunnel run thought-stream-tunnel
    ```

    You can also run the tunnel as a service to have it start automatically on boot. See the Cloudflare documentation for details.

### 7. Access Your Application

You should now be able to access your Thought Stream application from the internet at `https://your-subdomain.your-domain.com`.

### 8. Subscribing to Notifications

1.  Open the application in your browser.
2.  Click the "Subscribe to Notifications" button.
3.  Your browser will ask for permission to show notifications. Click "Allow".

You will now receive a push notification every time a new thought is posted.
