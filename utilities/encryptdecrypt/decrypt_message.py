import base64

from utilities.encryptdecrypt.shield_crypto import shield_decrypt

# =================================== Functions =======================================================================

def decrypt_message(session_key: bytes, ciphertext: str) -> str:
    try:
        decrypted = shield_decrypt(session_key, ciphertext)
        return decrypted if decrypted else ""
    except Exception as e:
        print(f"[DECRYPT ERROR] Decryption failed")
        return ""

def decrypt_bytes(session_key : bytes, encrypted_bytes :bytes):
    encrypted_str = encrypted_bytes.decode('utf-8')
    decrypted_b64 = decrypt_message(session_key, encrypted_str)
    return base64.b64decode(decrypted_b64)