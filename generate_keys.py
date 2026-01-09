import json
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Generate a private key
private_key = ec.generate_private_key(ec.SECP256R1())

# Get the public key
public_key = private_key.public_key()

# Serialize the private key to PEM format
private_key_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode('utf-8')

# Serialize the public key to PEM format
public_key_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode('utf-8')

# For web push, we need the raw public key in uncompressed format
public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Base64 encode the public key
public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).rstrip(b'=').decode('utf-8')


keys = {
    'private_key': private_key_pem,
    'public_key_pem': public_key_pem,
    'public_key_b64': public_key_b64
}

with open('vapid_keys.json', 'w') as f:
    json.dump(keys, f, indent=4)

print("Successfully generated and saved VAPID keys to vapid_keys.json")
print("\nShare this public key with the client:")
print(public_key_b64)
