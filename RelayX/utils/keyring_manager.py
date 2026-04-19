import keyring
from cryptography.fernet import Fernet

service_name = "RelayX"
key_name = "db_key"

def generate_key():
    key = Fernet.generate_key()
    keyring.set_password(service_name, key_name, key.decode())
    return key

def keyring_load_key():
    stored = keyring.get_password(service_name, key_name)
    if stored:
        return stored.encode()
    else:
        return generate_key()