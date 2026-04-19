from argon2.low_level import hash_secret_raw, Type
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

aad = b"RelayX-Token-Encryption|onion-invite"

def generate_key(password : bytes, salt):
    key = hash_secret_raw(
        secret=password, salt = salt,
        time_cost=3, memory_cost=65536, parallelism=2,
        hash_len=32, type=Type.ID
    )
    return key

def encrypt_token_bytes(password:bytes, plaintext:bytes) -> str:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = generate_key(password, salt)
    cipher = ChaCha20Poly1305(key)
    ciphertext = cipher.encrypt(nonce, plaintext, aad)
    payload = salt + nonce + ciphertext
    payload_b64 = base64.urlsafe_b64encode(payload).decode()
    return payload_b64

def decrypt_token_bytes(token_payload_b64:str, password:bytes):
    token_payload = base64.urlsafe_b64decode(token_payload_b64.encode())
    salt = token_payload[:16]
    nonce = token_payload[16:28]
    ciphertext = token_payload[28:]
    key = generate_key(password, salt)
    cipher = ChaCha20Poly1305(key)
    try:
        onion = cipher.decrypt(nonce, ciphertext, aad)
        return onion
    except Exception:
        pass
