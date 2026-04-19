"""             Encrypter module

Encrypts messages. uses helpers from shield crypto module
Part of Project RelayX, By Poojit Matukumalli
"""
import base64

from utilities.encryptdecrypt.shield_crypto import shield_encrypt

# =================================== Functions =======================================================================

def encrypt_message(chat_key: bytes, message: str) -> str:
    try:
        encrypted = shield_encrypt(chat_key, message)
        if not encrypted:
            raise RuntimeError("[ENCRYPT ERROR] Encryption failed")
        return encrypted
    except Exception as e:
        print(f"[ENCRYPT ERROR] {e}")
        return ""

def encrypt_bytes(session_key:bytes, raw : bytes) -> bytes:
    b64 = base64.b64encode(raw).decode('utf-8')
    encrypted_str = encrypt_message(session_key, b64)
    return encrypted_str.encode('utf-8')