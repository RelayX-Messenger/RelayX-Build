"""
Fetches contacts and blocked contacts
"""
from fastapi import APIRouter

from RelayX.database.crud import fetch_contacts, fetch_blocked_contacts
from RelayX.utils.config import user_onion


router = APIRouter()

@router.get("/contacts")
async def get_contacts():
    global user_onion
    try:
        contacts = await fetch_contacts(user_onion)
        return contacts
    except Exception as e:
        return {
            "status":"Failed",
            "msg" : f"[CONTACT FETCH ERROR]\n{str(e)}"     
        }

@router.get("/fetch_blocked")
async def get_blocked():
    try:
        blocked_contacts = await fetch_blocked_contacts()
        return blocked_contacts
    except Exception as e:
        return {"status" : "Failed", "msg" : f"[BLOCKED CONTACT FETCH ERROR]\n{e}"}