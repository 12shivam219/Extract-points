"""
Data persistence utilities for saving user preferences and settings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SettingsPersistence:
    """Handles saving and loading user settings."""
    
    SETTINGS_DIR = Path.home() / ".extract_points" / "settings"
    SETTINGS_FILE = SETTINGS_DIR / "user_settings.json"
    
    # Default settings
    DEFAULT_SETTINGS = {
        'points_per_cycle': 2,
        'deduplication_enabled': False,
        'deduplication_strictness': 'exact',  # 'exact' or 'fuzzy'
        'last_used_profile': None,
        'auto_map_cycles': True,
        'show_advanced_options': False,
        'preferred_export_format': 'docx',  # 'docx', 'pdf', or 'both'
        'session_history': [],  # Track last 5 sessions
    }
    
    def __init__(self):
        """Initialize settings persistence."""
        self.SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        try:
            if self.SETTINGS_FILE.exists():
                with open(self.SETTINGS_FILE, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = {**self.DEFAULT_SETTINGS, **loaded}
                    logger.debug(f"Loaded user settings from {self.SETTINGS_FILE}")
                    return settings
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
        
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Could not save settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self.settings[key] = value
        self.save_settings()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        return self.settings.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()
        logger.info("Settings reset to defaults")
    
    def add_to_history(self, item: str) -> None:
        """
        Add an item to session history (keeps last 5).
        
        Args:
            item: Description of action/file processed
        """
        history = self.settings.get('session_history', [])
        history.insert(0, item)
        # Keep only last 5 items
        self.settings['session_history'] = history[:5]
        self.save_settings()
    
    def get_history(self) -> list:
        """Get session history."""
        return self.settings.get('session_history', [])
    
    def clear_history(self) -> None:
        """Clear session history."""
        self.settings['session_history'] = []
        self.save_settings()


class RecentUsedManager:
    """Manages recently used files and settings."""
    
    RECENT_DIR = Path.home() / ".extract_points" / "recent"
    
    def __init__(self):
        """Initialize recent used manager."""
        self.RECENT_DIR.mkdir(parents=True, exist_ok=True)
    
    def save_recent_mapping(self, name: str, mapping: Dict) -> bool:
        """Save a recently used mapping configuration."""
        try:
            filepath = self.RECENT_DIR / f"{name}_recent.json"
            with open(filepath, 'w') as f:
                json.dump(mapping, f, indent=2)
            logger.debug(f"Saved recent mapping: {name}")
            return True
        except Exception as e:
            logger.error(f"Could not save recent mapping: {e}")
            return False
    
    def get_recent_mapping(self, name: str) -> Optional[Dict]:
        """Get a recently used mapping."""
        try:
            filepath = self.RECENT_DIR / f"{name}_recent.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load recent mapping: {e}")
        
        return None
    
    def list_recent_mappings(self) -> list:
        """List all recent mappings."""
        mappings = []
        try:
            if self.RECENT_DIR.exists():
                for filepath in sorted(self.RECENT_DIR.glob("*_recent.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                    name = filepath.stem.replace('_recent', '')
                    mappings.append({
                        'name': name,
                        'path': filepath,
                        'modified': filepath.stat().st_mtime
                    })
        except Exception as e:
            logger.warning(f"Could not list recent mappings: {e}")
        
        return mappings
    
    def clear_recent_mappings(self) -> bool:
        """Clear all recent mappings."""
        try:
            if self.RECENT_DIR.exists():
                for filepath in self.RECENT_DIR.glob("*_recent.json"):
                    filepath.unlink()
            logger.info("Recent mappings cleared")
            return True
        except Exception as e:
            logger.error(f"Could not clear recent mappings: {e}")
            return False
