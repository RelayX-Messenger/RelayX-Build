from cryptography.fernet import Fernet

from RelayX.utils.keyring_manager import keyring_load_key

key_material = keyring_load_key()
f = Fernet(key_material)

def db_encrypt(message : str):
    message_bytes = message.encode()
    encrypted = f.encrypt(message_bytes)
    return encrypted

def db_decrypt(message_bytes : bytes):
    message = message_bytes.decode()
    decrypted =f.decrypt(message)
    return decrypted