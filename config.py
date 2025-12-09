"""
Configuration management for the Nottorney addon
Handles storing and retrieving tokens, settings, etc.
"""

from aqt import mw
from datetime import datetime
import json
import os


class Config:
    """Manages addon configuration and authentication state"""
    
    def __init__(self):
        # Get the actual addon folder name dynamically
        # This will work regardless of whether it's "Nottorney_Addon", etc.
        addon_path = os.path.dirname(os.path.dirname(__file__))
        self.addon_name = os.path.basename(addon_path)
        
    def _get_config(self):
        """Get the addon config from Anki"""
        try:
            config = mw.addonManager.getConfig(self.addon_name)
            if config is None:
                # Return default config if none exists
                return self._get_default_config()
            return config
        except Exception:
            # If there's any error reading config, return defaults
            return self._get_default_config()
    
    def _get_default_config(self):
        """Get the default configuration"""
        return {
            "api_url": "https://ladvckxztcleljbiomcf.supabase.co/functions/v1",
            "auto_sync_enabled": True,
            "auto_sync_interval_hours": 1,
            "downloaded_decks": {},
            "access_token": None,
            "refresh_token": None,
            "expires_at": None,
            "user": None
        }
    
    def _save_config(self, data):
        """Save the addon config to Anki"""
        try:
            mw.addonManager.writeConfig(self.addon_name, data)
        except Exception as e:
            # If saving fails, we'll just continue
            # The config will be lost but the addon won't crash
            print(f"Warning: Failed to save config: {e}")
    
    # Authentication
    def save_tokens(self, access_token, refresh_token, expires_at):
        """Save authentication tokens"""
        cfg = self._get_config()
        cfg['access_token'] = access_token
        cfg['refresh_token'] = refresh_token
        cfg['expires_at'] = expires_at
        self._save_config(cfg)
    
    def get_access_token(self):
        """Get the current access token"""
        return self._get_config().get('access_token')
    
    def get_refresh_token(self):
        """Get the current refresh token"""
        return self._get_config().get('refresh_token')
    
    def get_token_expiry(self):
        """Get the token expiration timestamp"""
        return self._get_config().get('expires_at')
    
    def is_token_expired(self):
        """Check if the access token is expired"""
        expires_at = self.get_token_expiry()
        if not expires_at:
            return True
        return datetime.now().timestamp() >= expires_at
    
    def clear_tokens(self):
        """Clear all authentication tokens"""
        cfg = self._get_config()
        cfg.pop('access_token', None)
        cfg.pop('refresh_token', None)
        cfg.pop('expires_at', None)
        cfg.pop('user', None)
        self._save_config(cfg)
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return bool(self.get_access_token())
    
    # User data
    def save_user(self, user_data):
        """Save user information"""
        cfg = self._get_config()
        cfg['user'] = user_data
        self._save_config(cfg)
    
    def get_user(self):
        """Get saved user information"""
        return self._get_config().get('user')
    
    # API settings
    def get_api_url(self):
        """Get the API base URL"""
        return self._get_config().get('api_url', 
            'https://ladvckxztcleljbiomcf.supabase.co/functions/v1')
    
    def set_api_url(self, url):
        """Set the API base URL"""
        cfg = self._get_config()
        cfg['api_url'] = url
        self._save_config(cfg)
    
    # Downloaded decks tracking
    def save_downloaded_deck(self, deck_id, version, anki_deck_id):
        """Track a downloaded deck"""
        cfg = self._get_config()
        if 'downloaded_decks' not in cfg:
            cfg['downloaded_decks'] = {}
        
        cfg['downloaded_decks'][deck_id] = {
            'version': version,
            'anki_deck_id': anki_deck_id,
            'downloaded_at': datetime.now().isoformat()
        }
        self._save_config(cfg)
    
    def get_downloaded_decks(self):
        """Get list of downloaded decks"""
        return self._get_config().get('downloaded_decks', {})
    
    def is_deck_downloaded(self, deck_id):
        """Check if a deck is already downloaded"""
        return deck_id in self.get_downloaded_decks()
    
    def get_deck_version(self, deck_id):
        """Get the version of a downloaded deck"""
        decks = self.get_downloaded_decks()
        return decks.get(deck_id, {}).get('version')


# Global config instance
config = Config()