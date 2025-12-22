"""
Update checking service for AnkiPH addon
Checks for deck updates in the background and notifies users
Version: 2.2.0 - Fixed token expiry handling
"""

import threading
from aqt import mw
from aqt.utils import showInfo, tooltip
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .api_client import api, AnkiPHAPIError, set_access_token, ensure_valid_token
from .config import config
from .logger import logger


class UpdateChecker:
    """Handles checking for deck updates"""
    
    def __init__(self):
        self.checking = False
        self._checking_lock = threading.Lock()
    
    def should_check_updates(self) -> bool:
        """
        Determine if we should check for updates now
        
        Returns:
            True if enough time has passed since last check
        """
        if not config.is_logged_in():
            return False
        
        if not config.get_auto_check_updates():
            return False
        
        last_check = config.get_last_update_check()
        if not last_check:
            return True
        
        try:
            last_check_dt = datetime.fromisoformat(last_check)
            interval_hours = config.get_update_check_interval_hours()
            next_check = last_check_dt + timedelta(hours=interval_hours)
            
            return datetime.now() >= next_check
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing last check timestamp: {e}")
            return True
    
    def check_for_updates(self, silent: bool = False) -> Optional[Dict]:
        """
        Check for updates on all purchased decks
        """
        # Thread-safe check using context manager to ensure release
        if not self._checking_lock.acquire(blocking=False):
            logger.info("Update check already in progress")
            return None
        
        try:
            self.checking = True
            return self._do_check_updates(silent)
        finally:
            self.checking = False
            self._checking_lock.release()

    def _do_check_updates(self, silent: bool) -> Optional[Dict]:
        """Actual update check logic"""
        try:
            # Ensure we're logged in
            if not config.is_logged_in():
                if not silent:
                    showInfo("Please login first to check for updates.")
                return None
            
            # Try to refresh token if needed
            if not ensure_valid_token():
                if not silent:
                    showInfo("Please login first to check for updates.")
                return None
            
            if not silent:
                tooltip("Checking for deck updates...", period=2000)
            
            # Call API
            result = api.check_updates()
            
            # Update last check timestamp
            config.set_last_update_check()
            
            if not result.get('success'):
                error_msg = result.get('message', 'Failed to check updates')
                if not silent:
                    showInfo(f"Update check failed:\n{error_msg}")
                return None
            
            # Process results
            decks_with_updates = result.get('decks', [])
            
            # Build updates dict
            updates_dict = {}
            for deck_update in decks_with_updates:
                deck_id = deck_update.get('deck_id')
                has_update = deck_update.get('has_update', False)
                
                if has_update:
                    updates_dict[deck_id] = {
                        'deck_id': deck_id,
                        'current_version': deck_update.get('synced_version'),
                        'latest_version': deck_update.get('current_version'),
                        'has_update': True,
                        'update_type': 'standard',
                        'changelog_summary': 'Update available',
                        'title': deck_update.get('title'),
                        'checked_at': datetime.now().isoformat()
                    }
            
            # Save to config
            config.save_available_updates(updates_dict)
            
            # Show notification
            update_count = len(updates_dict)
            if update_count > 0:
                if update_count == 1:
                    msg = "1 deck update available!"
                else:
                    msg = f"{update_count} deck updates available!"
                
                tooltip(msg, period=3000)
                
                # Show detailed info if not silent
                if not silent:
                    self._show_update_summary(updates_dict)
            else:
                if not silent:
                    tooltip("All decks are up to date! ✓", period=2000)
            
            logger.info(f"Update check complete: {update_count} update(s) available")
            
            return updates_dict
        
        except AnkiPHAPIError as e:
            error_msg = str(e)
            if e.status_code == 401:
                error_msg = "Session expired. Please login again."
                config.clear_tokens()
            
            logger.error(f"Update check failed: {error_msg}")
            
            if not silent:
                showInfo(f"Failed to check for updates:\n{error_msg}")
            
            return None
        
        except Exception as e:
            logger.exception(f"Update check error: {e}")
            
            if not silent:
                showInfo(f"Update check failed:\n{str(e)}")
            
            return None

    def _show_update_summary(self, updates_dict: Dict):
        """
        Show a summary of available updates
        
        Args:
            updates_dict: Dict of deck updates
        """
        if not updates_dict:
            return
        
        # Build message
        lines = ["Available Updates:\n"]
        
        for deck_id, update_info in updates_dict.items():
            current = update_info.get('current_version', 'Unknown')
            latest = update_info.get('latest_version', 'Unknown')
            summary = update_info.get('changelog_summary', '')
            
            # Try to get deck name from downloaded decks
            downloaded = config.get_downloaded_decks()
            deck_name = "Unknown Deck"
            
            if deck_id in downloaded:
                # We don't have the name in config, just use ID
                deck_name = f"Deck {deck_id[:8]}"
            
            lines.append(f"• {deck_name}")
            lines.append(f"  {current} → {latest}")
            if summary:
                lines.append(f"  {summary}")
            lines.append("")
        
        lines.append("Open AnkiPH to update your decks.")
        
        showInfo("\n".join(lines))
    
    def get_update_info(self, deck_id: str) -> Optional[Dict]:
        """
        Get update info for a specific deck
        
        Args:
            deck_id: The deck ID
        
        Returns:
            Update info dict or None
        """
        updates = config.get_available_updates()
        return updates.get(str(deck_id))
    
    def has_updates_available(self) -> bool:
        """
        Check if any decks have updates available
        
        Returns:
            True if updates are available
        """
        updates = config.get_available_updates()
        return len(updates) > 0
    
    def get_update_count(self) -> int:
        """
        Get count of decks with updates available
        
        Returns:
            Number of decks with updates
        """
        updates = config.get_available_updates()
        return len(updates)
    
    def clear_update(self, deck_id: str):
        """
        Clear update notification for a deck (after updating)
        
        Args:
            deck_id: The deck ID
        """
        config.clear_update_for_deck(deck_id)
        logger.info(f"Cleared update notification for deck {deck_id}")
    
    def get_changelog(self, deck_id: str) -> Optional[List[Dict]]:
        """
        Get full changelog for a deck
        
        Args:
            deck_id: The deck ID
        
        Returns:
            List of version history entries or None
        """
        try:
            # Ensure we're logged in
            if not config.is_logged_in():
                return None
            
            # Set access token
            token = config.get_access_token()
            set_access_token(token)
            
            # Call API
            result = api.get_changelog(deck_id)
            
            if result.get('success'):
                return result.get('changelog', [])
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get changelog for {deck_id}: {e}")
            return None
    
    def auto_check_updates_if_needed(self):
        """Auto-check for updates if interval has passed"""
        if not self.should_check_updates():
            return
        
        logger.info("Auto-checking for updates...")
        
        # Check silently in background
        try:
            self.check_for_updates(silent=True)
        except Exception as e:
            logger.exception(f"Auto-update check failed (non-critical): {e}")
    
    def auto_apply_updates(self):
        """
        Automatically download and apply all available updates.
        Called on startup for hands-off sync experience.
        """
        updates = config.get_available_updates()
        
        if not updates:
            logger.info("No updates to auto-apply")
            return
        
        logger.info(f"Auto-applying {len(updates)} update(s)...")
        
        # Import locally to avoid circular dependency at module level
        from .deck_importer import import_deck_from_json
        
        success_count = 0
        fail_count = 0
        
        for deck_id, update_info in updates.items():
            try:
                # Refresh token before each download
                refresh_token = config.get_refresh_token()
                if refresh_token:
                    try:
                        result = api.refresh_token(refresh_token)
                        if result.get('success'):
                            new_token = result.get('access_token')
                            new_refresh = result.get('refresh_token', refresh_token)
                            expires_at = result.get('expires_at')
                            
                            if new_token:
                                config.save_tokens(new_token, new_refresh, expires_at)
                                set_access_token(new_token)
                    except Exception as e:
                        logger.warning(f"Token refresh failed during auto-update: {e}")
                
                # Set access token
                token = config.get_access_token()
                if not token:
                    logger.error("No access token available for auto-update")
                    fail_count += 1
                    continue
                
                set_access_token(token)
                
                # Get deck data (JSON) directly
                result = api.download_deck(deck_id)
                
                if not result.get('success'):
                    logger.error(f"Failed to get deck data for {deck_id}: {result.get('error', 'Unknown error')}")
                    fail_count += 1
                    continue
                
                # Import the deck (synchronous for background operation)
                deck_name = update_info.get('title') or f"Update_{deck_id[:8]}"
                logger.info(f"Syncing deck {deck_name}...")
                
                anki_deck_id = import_deck_from_json(result, deck_name)
                
                if not anki_deck_id:
                    logger.error(f"Failed to sync deck {deck_id} - import returned None")
                    fail_count += 1
                    continue
                
                # Update tracking
                new_version = update_info.get('latest_version', 'Unknown')
                config.save_downloaded_deck(
                    deck_id=deck_id,
                    version=new_version,
                    anki_deck_id=anki_deck_id,
                    title=update_info.get('title')
                )
                
                # Clear the update notification
                self.clear_update(deck_id)
                
                logger.info(f"Auto-updated deck {deck_id} to v{new_version}")
                success_count += 1
                
            except AnkiPHAPIError as e:
                logger.error(f"API error auto-updating deck {deck_id}: {e}")
                fail_count += 1
                continue
            except Exception as e:
                logger.exception(f"Failed to auto-update deck {deck_id}: {e}")
                fail_count += 1
                continue
        
        # Show summary
        if success_count > 0:
            tooltip(f"⚖️ AnkiPH: Synced {success_count} deck(s)", period=3000)
        
        if fail_count > 0:
            logger.warning(f"{fail_count} deck(s) failed to auto-update")


# Global update checker instance
update_checker = UpdateChecker()