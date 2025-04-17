from typing import Optional
import uuid
from datetime import datetime, timedelta

# Simple in-memory session storage
active_sessions = {}

def create_session(username: str) -> str:
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=1)
    }
    return session_id

def delete_session(session_id: Optional[str] = None) -> Optional[str]:
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    return None

def get_session(session_id: str) -> Optional[dict]:
    if session_id not in active_sessions:
        return None
    
    session = active_sessions[session_id]
    if datetime.now() > session["expires_at"]:
        del active_sessions[session_id]
        return None
    
    return session

def get_current_user(session_id: Optional[str] = None) -> Optional[str]:
    if not session_id:
        return None
    
    session = get_session(session_id)
    if not session:
        return None
    
    return session["username"] 