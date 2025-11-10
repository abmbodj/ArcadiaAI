"""
Session and user management for ArchieAI.
Handles user accounts, session storage, and chat history.
"""
import os
import json
import secrets
import re
from datetime import datetime
from typing import Optional, Dict, List
from werkzeug.security import generate_password_hash, check_password_hash


class SessionManager:
    """Manages user accounts and chat sessions with JSON file storage."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.sessions_dir = os.path.join(data_dir, "sessions")
        
        # Ensure directories exist
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        # Initialize users file if it doesn't exist
        if not os.path.exists(self.users_file):
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
    
    def _load_users(self) -> Dict:
        """Load users from JSON file."""
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # File doesn't exist yet, return empty dict
            return {}
        except json.JSONDecodeError as e:
            # File is corrupted, log error and return empty dict
            print(f"Warning: users.json is corrupted: {e}")
            return {}
    
    def _save_users(self, users: Dict):
        """Save users to JSON file."""
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)

    def create_user(self, email: str, password: str, ip_address: str, device_info: str) -> bool:
        """Create a new user account."""
        users = self._load_users()
        
        if email in users:
            return False
        
        users[email] = {
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now().isoformat(),
            "ip_address": ip_address,
            "device_info": device_info,
            "sessions": []
        }
        
        self._save_users(users)
        return True
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """Authenticate a user with email and password."""
        users = self._load_users()
        
        if email not in users:
            return False
        
        return check_password_hash(users[email]["password_hash"], password)
    
    def _is_valid_session_id(self, session_id: str) -> bool:
        """Validate that session_id is safe to use in file paths."""
        # Only allow alphanumeric, dash, and underscore characters
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', session_id)) and len(session_id) <= 64
    
    def get_user_sessions(self, email: str) -> List[str]:
        """Get all session IDs for a user."""
        users = self._load_users()
        
        if email not in users:
            return []
        
        return users[email].get("sessions", [])
    
    def create_session(self, user_email: Optional[str] = None) -> str:
        """Create a new chat session with cryptographically secure ID."""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "session_id": session_id,
            "user_email": user_email,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        
        # Add session to user's session list if user is logged in
        if user_email:
            users = self._load_users()
            if user_email in users:
                if "sessions" not in users[user_email]:
                    users[user_email]["sessions"] = []
                users[user_email]["sessions"].append(session_id)
                self._save_users(users)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Load a session from file."""
        if not self._is_valid_session_id(session_id):
            print(f"Warning: invalid session_id format: {session_id}")
            return None
        
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            return None
        
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            print(f"Warning: session {session_id} is corrupted: {e}")
            return None
    
    def save_session(self, session_id: str, session_data: Dict):
        """Save session data to file."""
        if not self._is_valid_session_id(session_id):
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to a session."""
        session_data = self.get_session(session_id)
        
        if session_data is None:
            # Create new session if it doesn't exist
            session_data = {
                "session_id": session_id,
                "user_email": None,
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        session_data["messages"].append(message)
        self.save_session(session_id, session_data)
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        session_data = self.get_session(session_id)
        
        if session_data is None:
            return []
        
        return session_data.get("messages", [])[:10]
    
    def delete_session(self, session_id: str, user_email: Optional[str] = None) -> bool:
        """Delete a chat session."""
        if not self._is_valid_session_id(session_id):
            print(f"Warning: invalid session_id format: {session_id}")
            return False
        
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            return False
        
        # Remove from user's session list if applicable
        if user_email:
            users = self._load_users()
            if user_email in users and "sessions" in users[user_email]:
                if session_id in users[user_email]["sessions"]:
                    users[user_email]["sessions"].remove(session_id)
                    self._save_users(users)
        
        # Delete the session file
        os.remove(session_file)
        return True
    
    def get_all_user_sessions_with_preview(self, email: str) -> List[Dict]:
        """Get all sessions for a user with message preview."""
        session_ids = self.get_user_sessions(email)
        sessions = []
        
        for session_id in session_ids:
            session_data = self.get_session(session_id)
            if session_data:
                messages = session_data.get("messages", [])
                preview = ""
                if messages:
                    # Get first user message as preview
                    for msg in messages:
                        if msg["role"] == "user":
                            preview = msg["content"][:100]
                            break
                
                sessions.append({
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "preview": preview,
                    "message_count": len(messages)
                })
        
        return sessions
