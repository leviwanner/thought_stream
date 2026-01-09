import json
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_and_save_keys():
    """
    Generates a new VAPID key pair and saves it to vapid_keys.json
    in the formats required by the application.
    """
    print("Generating new VAPID key pair...")
    
    # Generate a private key using the P-256 curve
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # --- Private Key (for pywebpush) ---
    # Serialize to PEM format. This is what pywebpush needs.
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # --- Public Key (for the browser) ---
    # Get the raw, uncompressed public key bytes
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    # URL-safe Base64 encode the public key bytes. This is what the browser needs.
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).rstrip(b'=').decode('utf-8')

    keys = {
        'private_key': private_key_pem,
        'public_key_b64': public_key_b64
    }

    with open('vapid_keys.json', 'w') as f:
        json.dump(keys, f, indent=4)

    print("Successfully generated and saved new keys to vapid_keys.json")
    print("\nPublic Key (for browser):")
    print(public_key_b64)

if __name__ == '__main__':
    generate_and_save_keys()