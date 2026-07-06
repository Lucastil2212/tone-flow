"""Session history persistence with ring buffer."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class SessionHistory:
    """
    Manage session history with ring buffer (max 5 entries).
    
    Stores sessions in ~/ToneFlow/sessions.json
    """
    
    def __init__(self, max_sessions=5):
        """
        Initialize session history.
        
        Args:
            max_sessions: Maximum number of sessions to keep (default 5)
        """
        self.max_sessions = max_sessions
        
        # Data directory: ~/ToneFlow/
        self.data_dir = Path.home() / "ToneFlow"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.data_dir / "sessions.json"
        self.exports_dir = self.data_dir / "exports"
        self.exports_dir.mkdir(exist_ok=True)
        
        # Load existing history
        self.sessions = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load session history from disk."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return data.get('sessions', [])
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self):
        """Save session history to disk."""
        data = {'sessions': self.sessions}
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save session history: {e}")
    
    def add_session(
        self,
        preset_id: str,
        carrier_hz: float,
        beat_hz: float,
        mode: str,
        effects: Dict[str, Any],
        duration_sec: float,
        mood_pre: Optional[Dict[str, int]] = None,
        mood_post: Optional[Dict[str, int]] = None
    ):
        """
        Add a session to history.
        
        Args:
            preset_id: Preset identifier
            carrier_hz: Carrier frequency used
            beat_hz: Beat frequency used
            mode: 'binaural' or 'monaural'
            effects: Effects configuration dict
            duration_sec: Actual session duration in seconds
            mood_pre: Pre-session mood ratings (optional)
            mood_post: Post-session mood ratings (optional)
        """
        session = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'preset_id': preset_id,
            'carrier_hz': carrier_hz,
            'beat_hz': beat_hz,
            'mode': mode,
            'effects': effects,
            'duration_sec': duration_sec
        }
        
        # Add mood data if provided
        if mood_pre is not None:
            session['mood_pre'] = mood_pre
        if mood_post is not None:
            session['mood_post'] = mood_post
        
        # Add to history (ring buffer)
        self.sessions.append(session)
        
        # Keep only last max_sessions
        if len(self.sessions) > self.max_sessions:
            self.sessions = self.sessions[-self.max_sessions:]
        
        # Save to disk
        self._save_history()
    
    def get_recent_sessions(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent sessions.
        
        Args:
            count: Number of sessions to retrieve
            
        Returns:
            List of session dicts (most recent first)
        """
        return list(reversed(self.sessions[-count:]))
    
    def get_last_session(self) -> Optional[Dict[str, Any]]:
        """Get the most recent session, or None if empty."""
        if self.sessions:
            return self.sessions[-1]
        return None
    
    def clear_history(self):
        """Clear all session history."""
        self.sessions = []
        self._save_history()
    
    def get_export_path(self, filename: str) -> Path:
        """
        Get full path for an export file.
        
        Args:
            filename: Export filename
            
        Returns:
            Full path in exports directory
        """
        return self.exports_dir / filename
    
    def generate_export_filename(self, preset_id: str) -> str:
        """
        Generate a unique export filename.
        
        Args:
            preset_id: Preset identifier
            
        Returns:
            Filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"toneflow_{preset_id}_{timestamp}.wav"

