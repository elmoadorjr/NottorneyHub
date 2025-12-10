"""
Configuration management for the Nottorney addon
Handles storing and retrieving tokens, settings, etc.
NOW WITH UI MODE PREFERENCE SUPPORT
"""

from aqt import mw
from datetime import datetime
import json
import os


class Config:
    """Manages addon configuration and authentication state"""
    
    def __init__(self):
        # Use the package name from manifest.json
        self.addon_name = "Nottorney_Addon"
        self._config_cache = None
        self._cache_timestamp = 0
        
    def _get_config(self):
        """Get the addon config from Anki with caching"""
        try:
            # Use cache if less than 1 second old
            current_time = datetime.now().timestamp()
            if self._config_cache and (current_time - self._cache_timestamp) < 1:
                return self._config_cache
            
            config = mw.addonManager.getConfig(self.addon_name)
            if config is None:
                print(f"Config is None for {self.addon_name}, using defaults")
                config = self._get_default_config()
            
            # Update cache
            self._config_cache = config
            self._cache_timestamp = current_time
            
            return config
        except Exception as e:
            print(f"Error reading config for {self.addon_name}: {e}")
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
            "user": None,
            "ui_mode": "minimal"  # NEW: "minimal" or "classic"
        }
    
    def _save_config(self, data):
        """Save the addon config to Anki"""
        try:
            mw.addonManager.writeConfig(self.addon_name, data)
            
            # Update cache
            self._config_cache = data.copy()
            self._cache_timestamp = datetime.now().timestamp()
            
            print(f"Config saved successfully for {self.addon_name}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to save config for {self.addon_name}: {e}")
            
            # Clear cache on save failure
            self._config_cache = None
            self._cache_timestamp = 0
            
            return False
    
    def _invalidate_cache(self):
        """Invalidate the config cache"""
        self._config_cache = None
        self._cache_timestamp = 0
    
    # === UI MODE PREFERENCE (NEW) ===
    
    def get_ui_mode(self):
        """
        Get the user's preferred UI mode
        Returns: "minimal" or "classic"
        """
        mode = self._get_config().get('ui_mode', 'minimal')
        if mode not in ['minimal', 'classic']:
            mode = 'minimal'
        return mode
    
    def set_ui_mode(self, mode):
        """
        Set the user's preferred UI mode
        Args:
            mode: "minimal" or "classic"
        """
        if mode not in ['minimal', 'classic']:
            print(f"Warning: Invalid UI mode '{mode}', using 'minimal'")
            mode = 'minimal'
        
        cfg = self._get_config()
        cfg['ui_mode'] = mode
        
        success = self._save_config(cfg)
        
        if success:
            print(f"UI mode set to: {mode}")
        
        return success
    
    # === AUTHENTICATION ===
    
    def save_tokens(self, access_token, refresh_token, expires_at):
        """Save authentication tokens"""
        cfg = self._get_config()
        cfg['access_token'] = access_token
        cfg['refresh_token'] = refresh_token
        cfg['expires_at'] = expires_at
        
        success = self._save_config(cfg)
        
        if success:
            print(f"Tokens saved: expires_at={expires_at}")
            
            # Calculate and log expiry time
            if expires_at:
                try:
                    expiry_time = datetime.fromtimestamp(expires_at)
                    current_time = datetime.now()
                    time_until_expiry = expiry_time - current_time
                    print(f"Token will expire in {time_until_expiry}")
                except:
                    pass
        else:
            print("WARNING: Tokens may not have been saved properly")
        
        return success
    
    def get_access_token(self):
        """Get the current access token"""
        token = self._get_config().get('access_token')
        return token
    
    def get_refresh_token(self):
        """Get the current refresh token"""
        token = self._get_config().get('refresh_token')
        return token
    
    def get_token_expiry(self):
        """Get the token expiration timestamp"""
        return self._get_config().get('expires_at')
    
    def is_token_expired(self):
        """Check if the access token is expired"""
        expires_at = self.get_token_expiry()
        
        if not expires_at:
            return True
        
        # Add 5 minute buffer to avoid edge cases
        current_time = datetime.now().timestamp()
        buffer_seconds = 300  # 5 minutes
        
        is_expired = current_time >= (expires_at - buffer_seconds)
        
        return is_expired
    
    def get_token_time_remaining(self):
        """Get the time remaining before token expires (in seconds)"""
        expires_at = self.get_token_expiry()
        
        if not expires_at:
            return 0
        
        current_time = datetime.now().timestamp()
        return max(0, expires_at - current_time)
    
    def clear_tokens(self):
        """Clear all authentication tokens"""
        cfg = self._get_config()
        cfg['access_token'] = None
        cfg['refresh_token'] = None
        cfg['expires_at'] = None
        cfg['user'] = None
        
        success = self._save_config(cfg)
        
        if success:
            print("Tokens cleared successfully")
        else:
            print("WARNING: Tokens may not have been cleared properly")
        
        return success
    
    def is_logged_in(self):
        """Check if user is logged in with a valid token"""
        has_token = bool(self.get_access_token())
        return has_token
    
    # === USER DATA ===
    
    def save_user(self, user_data):
        """Save user information"""
        if not user_data:
            print("Warning: Attempting to save null user data")
            return False
        
        cfg = self._get_config()
        cfg['user'] = user_data
        
        success = self._save_config(cfg)
        
        if success:
            email = user_data.get('email', 'unknown')
            print(f"User saved: {email}")
        
        return success
    
    def get_user(self):
        """Get saved user information"""
        return self._get_config().get('user')
    
    # === API SETTINGS ===
    
    def get_api_url(self):
        """Get the API base URL"""
        url = self._get_config().get('api_url', 
            'https://ladvckxztcleljbiomcf.supabase.co/functions/v1')
        
        # Remove trailing slash if present
        return url.rstrip('/')
    
    def set_api_url(self, url):
        """Set the API base URL"""
        if not url:
            print("Warning: Attempting to set empty API URL")
            return False
        
        cfg = self._get_config()
        cfg['api_url'] = url.rstrip('/')
        
        return self._save_config(cfg)
    
    # === DOWNLOADED DECKS TRACKING ===
    
    def save_downloaded_deck(self, deck_id, version, anki_deck_id):
        """Track a downloaded deck"""
        if not deck_id:
            print("Warning: Attempting to save deck with no ID")
            return False
        
        cfg = self._get_config()
        
        if 'downloaded_decks' not in cfg:
            cfg['downloaded_decks'] = {}
        
        cfg['downloaded_decks'][deck_id] = {
            'version': version,
            'anki_deck_id': anki_deck_id,
            'downloaded_at': datetime.now().isoformat()
        }
        
        success = self._save_config(cfg)
        
        if success:
            print(f"Saved downloaded deck: {deck_id} v{version}")
        
        return success
    
    def get_downloaded_decks(self):
        """Get dictionary of downloaded decks"""
        decks = self._get_config().get('downloaded_decks', {})
        return decks if isinstance(decks, dict) else {}
    
    def is_deck_downloaded(self, deck_id):
        """Check if a deck is already downloaded"""
        if not deck_id:
            return False
        
        return deck_id in self.get_downloaded_decks()
    
    def get_deck_version(self, deck_id):
        """Get the version of a downloaded deck"""
        if not deck_id:
            return None
        
        decks = self.get_downloaded_decks()
        deck_info = decks.get(deck_id, {})
        return deck_info.get('version')
    
    def get_deck_anki_id(self, deck_id):
        """Get the Anki deck ID for a downloaded deck"""
        if not deck_id:
            return None
        
        decks = self.get_downloaded_decks()
        deck_info = decks.get(deck_id, {})
        return deck_info.get('anki_deck_id')
    
    def remove_downloaded_deck(self, deck_id):
        """Remove a deck from the downloaded decks list"""
        if not deck_id:
            return False
        
        cfg = self._get_config()
        
        if 'downloaded_decks' not in cfg:
            return True
        
        if deck_id in cfg['downloaded_decks']:
            del cfg['downloaded_decks'][deck_id]
            success = self._save_config(cfg)
            
            if success:
                print(f"Removed deck from tracking: {deck_id}")
            
            return success
        
        return True
    
    # === AUTO-SYNC SETTINGS ===
    
    def get_auto_sync_enabled(self):
        """Check if auto-sync is enabled"""
        return self._get_config().get('auto_sync_enabled', True)
    
    def set_auto_sync_enabled(self, enabled):
        """Enable or disable auto-sync"""
        cfg = self._get_config()
        cfg['auto_sync_enabled'] = bool(enabled)
        return self._save_config(cfg)
    
    def get_auto_sync_interval(self):
        """Get auto-sync interval in hours"""
        return self._get_config().get('auto_sync_interval_hours', 1)
    
    def set_auto_sync_interval(self, hours):
        """Set auto-sync interval in hours"""
        cfg = self._get_config()
        cfg['auto_sync_interval_hours'] = max(1, int(hours))
        return self._save_config(cfg)


# Global config instance
config = Config()