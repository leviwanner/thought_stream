import json
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_and_save_keys():
    """
    Generates a new VAPID key pair and saves it to vapid_keys.json
    in formats required by the application.
    """
    print("Generating new VAPID key pair...")
    
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # --- Private Key (for pywebpush) ---
    # Get the raw private key bytes (DER format)
    private_key_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    # Base64 encode the raw bytes into a single-line string for JSON
    private_key_b64 = base64.b64encode(private_key_der).decode('utf-8')

    # --- Public Key (for the browser) ---
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).rstrip(b'=').decode('utf-8')

    keys = {
        'private_key': private_key_b64, # Now a single-line base64 string
        'public_key_b64': public_key_b64
    }

    with open('vapid_keys.json', 'w') as f:
        json.dump(keys, f, indent=4)

    print("Successfully generated and saved new keys to vapid_keys.json in the correct format.")

if __name__ == '__main__':
    generate_and_save_keys()
