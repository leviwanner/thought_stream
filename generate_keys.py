import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_and_save_keys():
    """
    Generates a new VAPID key pair and saves them to standard files.
    - vapid_private.pem: The private key in PEM format.
    - vapid_public.txt: The public key in URL-safe Base64 format.
    """
    print("Generating new VAPID key pair...")
    
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # --- Private Key (for pywebpush) ---
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open('vapid_private.pem', 'wb') as f:
        f.write(private_pem)
    print("Successfully saved private key to vapid_private.pem")

    # --- Public Key (for the browser) ---
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).rstrip(b'=').decode('utf-8')
    with open('vapid_public.txt', 'w') as f:
        f.write(public_key_b64)
    print("Successfully saved public key to vapid_public.txt")

if __name__ == '__main__':
    generate_and_save_keys()