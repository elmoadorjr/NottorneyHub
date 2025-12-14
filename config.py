"""
Configuration management for the Nottorney addon
FIXED: Better error handling and cache management
"""

from aqt import mw
from datetime import datetime
import json


class Config:
    """Manages addon configuration and authentication state"""
    
    def __init__(self):
        self.addon_name = "Nottorney_Addon"
        self._config_cache = None
        self._cache_timestamp = 0
        self._cache_timeout = 1.0  # 1 second cache
        
    def _get_config(self):
        """Get the addon config from Anki with caching"""
        try:
            # Use cache if less than timeout seconds old
            current_time = datetime.now().timestamp()
            if self._config_cache and (current_time - self._cache_timestamp) < self._cache_timeout:
                return self._config_cache
            
            # Get config from Anki
            config = mw.addonManager.getConfig(self.addon_name)
            
            if config is None:
                print(f"⚠ Config is None for {self.addon_name}, using defaults")
                config = self._get_default_config()
                # Save default config
                self._save_config(config)
            
            # Ensure all required keys exist
            default = self._get_default_config()
            for key, value in default.items():
                if key not in config:
                    config[key] = value
            
            # Update cache
            self._config_cache = config
            self._cache_timestamp = current_time
            
            return config
            
        except Exception as e:
            print(f"✗ Error reading config for {self.addon_name}: {e}")
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
            "ui_mode": "minimal",
            "last_notification_check": None,
            "unread_notification_count": 0
        }
    
    def _save_config(self, data):
        """Save the addon config to Anki"""
        try:
            # Make a deep copy to avoid reference issues
            data_to_save = json.loads(json.dumps(data, default=str))
            
            # Write to Anki
            mw.addonManager.writeConfig(self.addon_name, data_to_save)
            
            # Invalidate cache after save
            self._config_cache = None
            self._cache_timestamp = 0
            
            return True
            
        except Exception as e:
            print(f"✗ ERROR: Failed to save config: {e}")
            self._config_cache = None
            self._cache_timestamp = 0
            return False
    
    def _invalidate_cache(self):
        """Invalidate the config cache"""
        self._config_cache = None
        self._cache_timestamp = 0
    
    # === AUTHENTICATION ===
    
    def save_tokens(self, access_token, refresh_token, expires_at):
        """Save authentication tokens"""
        cfg = self._get_config()
        cfg['access_token'] = access_token
        cfg['refresh_token'] = refresh_token
        cfg['expires_at'] = expires_at
        
        success = self._save_config(cfg)
        if success:
            print(f"✓ Tokens saved: expires_at={expires_at}")
        else:
            print(f"✗ Failed to save tokens")
        return success
    
    def get_access_token(self):
        """Get the current access token"""
        return self._get_config().get('access_token')
    
    def get_refresh_token(self):
        """Get the current refresh token"""
        return self._get_config().get('refresh_token')
    
    def set_access_token(self, token):
        """Set the access token"""
        cfg = self._get_config()
        cfg['access_token'] = token
        return self._save_config(cfg)
    
    def is_logged_in(self):
        """Check if user is logged in with a valid token"""
        token = self.get_access_token()
        return bool(token)
    
    def clear_tokens(self):
        """Clear all authentication tokens"""
        cfg = self._get_config()
        cfg['access_token'] = None
        cfg['refresh_token'] = None
        cfg['expires_at'] = None
        cfg['user'] = None
        
        success = self._save_config(cfg)
        if success:
            print("✓ Tokens cleared successfully")
        else:
            print("✗ Failed to clear tokens")
        return success
    
    # === DOWNLOADED DECKS TRACKING ===
    
    def save_downloaded_deck(self, deck_id, version, anki_deck_id):
        """Track a downloaded deck"""
        if not deck_id:
            print("✗ Cannot save deck: no deck_id provided")
            return False
        
        # Ensure anki_deck_id is an integer
        try:
            anki_deck_id = int(anki_deck_id)
        except (ValueError, TypeError) as e:
            print(f"✗ Cannot save deck: invalid anki_deck_id '{anki_deck_id}' ({e})")
            return False
        
        cfg = self._get_config()
        
        if 'downloaded_decks' not in cfg or not isinstance(cfg['downloaded_decks'], dict):
            cfg['downloaded_decks'] = {}
        
        # Save deck info
        cfg['downloaded_decks'][str(deck_id)] = {
            'version': str(version),
            'anki_deck_id': anki_deck_id,
            'downloaded_at': datetime.now().isoformat()
        }
        
        success = self._save_config(cfg)
        
        if success:
            print(f"✓ Saved deck: {deck_id} v{version} (Anki ID: {anki_deck_id})")
        else:
            print(f"✗ Failed to save deck: {deck_id}")
        
        return success
    
    def get_downloaded_decks(self):
        """Get dictionary of downloaded decks"""
        self._invalidate_cache()
        cfg = self._get_config()
        decks = cfg.get('downloaded_decks', {})
        
        # Ensure it's a dictionary
        if not isinstance(decks, dict):
            print(f"⚠ downloaded_decks is not a dict, resetting")
            decks = {}
        
        print(f"Retrieved {len(decks)} tracked deck(s)")
        return decks
    
    def is_deck_downloaded(self, deck_id):
        """Check if a deck is downloaded"""
        if not deck_id:
            return False
        
        downloaded_decks = self.get_downloaded_decks()
        return str(deck_id) in downloaded_decks
    
    def get_deck_anki_id(self, deck_id):
        """Get the Anki deck ID for a downloaded deck"""
        if not deck_id:
            return None
        
        decks = self.get_downloaded_decks()
        deck_info = decks.get(str(deck_id), {})
        anki_deck_id = deck_info.get('anki_deck_id')
        
        if anki_deck_id is not None:
            try:
                return int(anki_deck_id)
            except (ValueError, TypeError):
                print(f"✗ Invalid anki_deck_id: {anki_deck_id}")
                return None
        
        return None
    
    def get_deck_version(self, deck_id):
        """Get the version of a downloaded deck"""
        if not deck_id:
            return None
        
        decks = self.get_downloaded_decks()
        deck_info = decks.get(str(deck_id), {})
        return deck_info.get('version')
    
    def remove_downloaded_deck(self, deck_id):
        """Remove a deck from tracking"""
        if not deck_id:
            print(f"✗ Cannot remove deck: no deck_id provided")
            return False
        
        print(f"Removing deck from tracking: {deck_id}")
        
        self._invalidate_cache()
        cfg = self._get_config()
        
        if 'downloaded_decks' not in cfg or not isinstance(cfg['downloaded_decks'], dict):
            print(f"✓ Deck {deck_id} not tracked (no tracking data)")
            return True
        
        deck_id_str = str(deck_id)
        
        if deck_id_str not in cfg['downloaded_decks']:
            print(f"✓ Deck {deck_id} not tracked (already removed)")
            return True
        
        # Remove from tracking
        del cfg['downloaded_decks'][deck_id_str]
        
        success = self._save_config(cfg)
        
        if success:
            print(f"✓ Removed deck from tracking: {deck_id}")
        else:
            print(f"✗ Failed to remove deck: {deck_id}")
        
        return success
    
    # === SETTINGS ===
    
    def get_auto_sync_enabled(self):
        """Check if auto-sync is enabled"""
        return self._get_config().get('auto_sync_enabled', True)
    
    def set_auto_sync_enabled(self, enabled):
        """Set auto-sync enabled state"""
        cfg = self._get_config()
        cfg['auto_sync_enabled'] = bool(enabled)
        return self._save_config(cfg)


# Global config instance
config = Config()