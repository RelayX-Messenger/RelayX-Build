from pydantic import BaseModel

class ConnectModel(BaseModel):
    recipient_onion : str
class SendModel(BaseModel):
    msg : str
    recipient_onion : str
class ContactFetch(BaseModel):
    user_onion : str
class ClearChat(BaseModel):
    user_onion1 : str
    user_onion2 : str
class DeleteChat(BaseModel):
    msg_id : str

class BlockStatus(BaseModel):
    onion : str
    block_status : bool

class DeleteAccont(BaseModel):
    confirm : bool

class CreateToken(BaseModel):
    password : str

class ReadToken(BaseModel):
    token_path : str
    password : str
    display_name : str