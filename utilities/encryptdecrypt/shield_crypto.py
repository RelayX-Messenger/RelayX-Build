"""             Shield Crypto module

Helpers for Encrypt and decrypt functions
"""
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

# =========================================== Configuration ==============================================================

AESGCM_KEY_SIZE = 32          # 256-bit AES-GCM
AESGCM_NONCE_SIZE = 12        # recommended nonce size for GCM
HKDF_INFO = b"RelayX-ephemeral-session-key"  # context string for domain separation

# =================================== Functions =======================================================================

def derive_shield_key(shared_key: bytes, nonce_a: bytes, nonce_b: bytes) -> bytes:
    salt = nonce_a + nonce_b

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=HKDF_INFO,
    )
    return hkdf.derive(shared_key)

def derive_AEAD_envelope(env_bytes, session_key):
    nonce = os.urandom(12)
    aad = b"RelayX-AEAD-envelope"
    aesgcm = AESGCM(session_key)
    ciphertext = aesgcm.encrypt(nonce, env_bytes, aad)
    payload = nonce + ciphertext
    return payload

def verify_AEAD_envelope(payload, session_key):
    nonce = payload[:12]
    ciphertext = payload[12:]
    aad = b"RelayX-AEAD-envelope"
    aesgcm = AESGCM(session_key)
    decrypted = aesgcm.decrypt(nonce, ciphertext, aad)
    return decrypted

# ----------------------------------------------------------------------------------------------------

#                             WARNING
# DO NOT CHANGE ASSOCIATED DATA UNLESS ALL YOUR CONTACTS DO THE SAME.
# CHANGING IT WILL CAUSE DECRYPTION COMMITTING SUICIDE LIKE MY SANITY.

def shield_encrypt(key: bytes, plaintext: str, associated_data = b"RelayX-Message-AD|Layer-0") -> str: 
    # Encrypts the plaintext using AES-GCM and returns urlsafe-base64 str.
    try:
        aesgcm = AESGCM(key)
        nonce = os.urandom(AESGCM_NONCE_SIZE)
        ad_bytes = associated_data
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), associated_data=ad_bytes)
        payload = nonce + ciphertext
        return base64.urlsafe_b64encode(payload).decode()
    except Exception as e:
        print(f"[SHIELD ENCRYPT ERROR], {e}")
        return

# ----------------------------------------------------------------------------------------------------

def shield_decrypt(key: bytes, encoded: str, associated_data = b"RelayX-Message-AD|Layer-0") -> str: 
    # Decrypts the urlsafe-base64 (nonce || ciphertext). On failure, this thing returns empty string.
    try:
        payload = base64.urlsafe_b64decode(encoded)
        if len(payload) < AESGCM_NONCE_SIZE + 16:  # 16 is minimum tag size
            raise ValueError("payload too short")
        nonce = payload[:AESGCM_NONCE_SIZE]
        ciphertext = payload[AESGCM_NONCE_SIZE:]
        aesgcm = AESGCM(key)
        ad_bytes = associated_data
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=ad_bytes)
        return plaintext.decode()
    except Exception as e:
        print(f"[SHIELD DECRYPT ERROR]")
        return