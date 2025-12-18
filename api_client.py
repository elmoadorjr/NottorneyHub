"""
Robust API client for AnkiPH Add-on
ENHANCED: Added update checking, notifications, and AnkiHub-parity endpoints
ENHANCED: Added tiered access support (AccessTier enum and access control)
Version: 3.1.0
"""

from __future__ import annotations
import json
from typing import Any, Dict, Optional, List
from enum import Enum
from datetime import datetime
import webbrowser

API_BASE = "https://ladvckxztcleljbiomcf.supabase.co/functions/v1"

try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error
    _HAS_REQUESTS = False


# === TIERED ACCESS SYSTEM (v3.0) ===

class AccessTier(Enum):
    """User access tier for AnkiPH"""
    COLLECTION_OWNER = "collection_owner"  # Full access, owns decks forever
    SUBSCRIBER = "subscriber"              # Full access via subscription
    FREE_TIER = "free_tier"                # Limited to is_free decks only
    LEGACY = "legacy_purchase"             # Individual deck purchases


def check_access(user_data: dict, deck: dict) -> Optional[AccessTier]:
    """
    Determine user's access tier for a specific deck.
    
    Args:
        user_data: Dict with owns_collection, has_subscription, subscription_expires_at
        deck: Dict with access_type field from API response
    
    Returns:
        AccessTier enum value, or None if no access
    """
    # Tier 1: Collection owners get everything
    if user_data.get("owns_collection"):
        return AccessTier.COLLECTION_OWNER
    
    # Tier 2: Active subscribers get everything
    if user_data.get("has_subscription"):
        expires = user_data.get("subscription_expires_at")
        if expires:
            try:
                expiry = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                if expiry > datetime.now(expiry.tzinfo):
                    return AccessTier.SUBSCRIBER
            except (ValueError, TypeError):
                # If can't parse, assume still valid
                return AccessTier.SUBSCRIBER
        else:
            # No expiry set, assume active
            return AccessTier.SUBSCRIBER
    
    # Tier 3: Free tier - only is_free subdecks
    access_type = deck.get("access_type", "")
    if access_type == "free_tier":
        return AccessTier.FREE_TIER
    
    # Tier 4: Legacy individual purchases
    if access_type == "legacy_purchase":
        return AccessTier.LEGACY
    
    return None  # No access


def can_sync_updates(tier: Optional[AccessTier]) -> bool:
    """
    Check if user's tier allows syncing updates.
    Free tier users cannot sync updates - they only get initial download.
    
    Args:
        tier: The user's AccessTier
    
    Returns:
        True if user can sync updates, False otherwise
    """
    if tier is None:
        return False
    return tier in [AccessTier.COLLECTION_OWNER, AccessTier.SUBSCRIBER, AccessTier.LEGACY]


def show_upgrade_prompt():
    """
    Show upgrade dialog when user tries to access paid content.
    Opens browser to collection purchase or subscription page.
    """
    try:
        from aqt.qt import QMessageBox
        from aqt import mw
        
        dialog = QMessageBox(mw)
        dialog.setWindowTitle("Upgrade Required")
        dialog.setText(
            "This deck requires a AnkiPH subscription or Collection purchase.\n\n"
            "\u2022 Collection: \u20b11,000 one-time (own all decks forever)\n"
            "\u2022 AnkiPH: \u20b1149/month (sync all decks)\n"
        )
        dialog.setIcon(QMessageBox.Icon.Information)
        
        collection_btn = dialog.addButton("Get Collection", QMessageBox.ButtonRole.ActionRole)
        subscribe_btn = dialog.addButton("Subscribe", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        dialog.exec()
        
        clicked = dialog.clickedButton()
        if clicked == collection_btn:
            webbrowser.open("https://nottorney.com/collection")
        elif clicked == subscribe_btn:
            webbrowser.open("https://nottorney.com/premium")
    except Exception as e:
        print(f"\u2717 Failed to show upgrade prompt: {e}")


class AnkiPHAPIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class ApiClient:
    """API client for AnkiPH backend"""
    
    def __init__(self, access_token: Optional[str] = None, base_url: str = API_BASE):
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")

    def _headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Build request headers"""
        headers = {"Content-Type": "application/json"}
        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _full_url(self, path: str) -> str:
        """Build full URL from path"""
        if path.startswith("/"):
            path = path[1:]
        return f"{self.base_url}/{path}"

    def post(self, path: str, json_body: Optional[Dict[str, Any]] = None, 
             require_auth: bool = True, timeout: int = 30) -> Any:
        """Make POST request to API"""
        url = self._full_url(path)
        headers = self._headers(include_auth=require_auth)

        if _HAS_REQUESTS:
            return self._post_with_requests(url, headers, json_body, timeout)
        else:
            return self._post_with_urllib(url, headers, json_body, timeout)

    def _post_with_requests(self, url: str, headers: Dict[str, str], 
                           json_body: Optional[Dict[str, Any]], timeout: int) -> Any:
        """POST using requests library"""
        try:
            resp = requests.post(url, headers=headers, json=json_body or {}, timeout=timeout)
        except requests.Timeout:
            raise AnkiPHAPIError("Request timed out. Please check your internet connection.")
        except requests.ConnectionError:
            raise AnkiPHAPIError("Connection failed. Please check your internet connection.")
        except Exception as e:
            raise AnkiPHAPIError(f"Network error: {e}") from e

        # Parse response
        try:
            data = resp.json()
        except Exception: 
            text = resp.text if hasattr(resp, "text") else ""
            raise AnkiPHAPIError(
                f"Invalid response from server (HTTP {resp.status_code})", 
                status_code=resp.status_code, 
                details=text[:500]
            )

        # Check for errors
        if not resp.ok:
            err_msg = None
            if isinstance(data, dict):
                err_msg = data.get("error") or data.get("message") or data.get("detail")
            
            if not err_msg:
                err_msg = f"HTTP {resp.status_code} error"
            
            raise AnkiPHAPIError(err_msg, status_code=resp.status_code, details=data)

        return data

    def _post_with_urllib(self, url: str, headers: Dict[str, str], 
                         json_body: Optional[Dict[str, Any]], timeout: int) -> Any:
        """POST using urllib (fallback)"""
        try:
            req_data = (json.dumps(json_body or {})).encode("utf-8")
            req = _urllib_request.Request(url, data=req_data, headers=headers, method="POST")
            
            with _urllib_request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                
                try:
                    data = json.loads(raw.decode("utf-8"))
                except Exception:
                    raise AnkiPHAPIError(
                        "Invalid JSON response from server", 
                        status_code=resp.getcode(), 
                        details=raw[:500]
                    )
                
                if resp.getcode() >= 400:
                    err_msg = data.get("error") if isinstance(data, dict) else None
                    raise AnkiPHAPIError(
                        err_msg or f"HTTP {resp.getcode()}", 
                        status_code=resp.getcode(), 
                        details=data
                    )
                
                return data
                
        except _urllib_error.HTTPError as he:
            try:
                body = he.read()
                parsed = json.loads(body.decode("utf-8"))
                err_msg = parsed.get("error") if isinstance(parsed, dict) else None
            except Exception:
                parsed = None
                err_msg = None
            
            raise AnkiPHAPIError(
                err_msg or f"HTTP {getattr(he, 'code', 'error')}", 
                status_code=getattr(he, "code", None), 
                details=parsed or str(he)
            ) from he
            
        except _urllib_error.URLError as ue:
            raise AnkiPHAPIError(f"Connection error: {ue}") from ue
            
        except Exception as e:
            raise AnkiPHAPIError(f"Network error: {e}") from e

    # === AUTHENTICATION ENDPOINTS ===
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login with email and password"""
        return self.post(
            "/addon-login", 
            json_body={"email": email, "password": password}, 
            require_auth=False
        )

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        return self.post(
            "/addon-refresh-token", 
            json_body={"refresh_token": refresh_token}, 
            require_auth=False
        )

    # === DECK ENDPOINTS ===
    
    def get_purchased_decks(self) -> Any:
        """Get user's purchased decks"""
        return self.post("/addon-get-purchases")

    def browse_decks(self, subject: Optional[str] = None, search: Optional[str] = None) -> Any:
        """
        Browse available decks
        
        Args:
            subject: Optional subject filter
            search: Optional search query
        
        Returns:
            API response with decks list
        """
        json_body = {"action": "list"}
        
        if subject:
            json_body["subject"] = subject
        if search:
            json_body["search"] = search
        
        return self.post("/addon-browse-decks", json_body=json_body)

    def download_deck(self, deck_id: str) -> Any:
        """Get download URL for a deck"""
        return self.post("/addon-download-deck", json_body={"deck_id": deck_id})

    def batch_download_decks(self, deck_ids: List[str]) -> Any:
        """
        Download multiple decks at once (max 10 per API docs)
        
        Args:
            deck_ids: List of deck IDs to download (max 10)
        
        Returns:
            API response with download URLs for each deck
        """
        if len(deck_ids) > 10:
            raise ValueError("Maximum 10 decks per batch download")
        
        return self.post("/addon-batch-download", json_body={"deck_ids": deck_ids})

    def download_deck_file(self, download_url: str) -> bytes:
        """Download deck file from signed URL"""
        if not download_url:
            raise AnkiPHAPIError("Download URL is required")

        if not _HAS_REQUESTS: 
            # Use urllib to fetch bytes
            try:
                req = _urllib_request.Request(download_url, method="GET")
                with _urllib_request.urlopen(req, timeout=120) as resp:
                    content = resp.read()
                    if len(content) == 0:
                        raise AnkiPHAPIError("Downloaded file is empty")
                    return content
            except Exception as e:
                raise AnkiPHAPIError(f"Network error while downloading deck: {e}") from e

        # Use requests library
        try:
            response = requests.get(download_url, timeout=120, stream=True, allow_redirects=True)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("Content-Type", "").lower()
            
            # Detect HTML/JSON error pages
            if "text/html" in content_type or "application/json" in content_type:
                try:
                    text = response.text[:1000]
                    if "error" in text.lower() or "expired" in text.lower():
                        raise AnkiPHAPIError(
                            "Download URL may be expired or invalid. Please try again."
                        )
                except Exception:
                    pass
                raise AnkiPHAPIError(
                    f"Received {content_type} instead of a deck file. URL may be expired."
                )

            # Check for valid deck file types
            valid_types = ("application/zip", "application/octet-stream", 
                          "application/x-zip-compressed", "binary/octet-stream")
            
            if content_type and not any(v in content_type for v in valid_types):
                print(f"⚠ Warning: unexpected content-type: {content_type}")

            # Download content
            content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: 
                    content.extend(chunk)

            if len(content) == 0:
                raise AnkiPHAPIError("Downloaded file is empty")

            # Quick ZIP signature check (PK magic bytes)
            if len(content) >= 4:
                if content[:2] != b"PK":
                    print("⚠ Warning: downloaded file does not appear to be a ZIP file")

            return bytes(content)
            
        except requests.HTTPError as he:
            raise AnkiPHAPIError(
                f"HTTP error while downloading deck: {he}", 
                status_code=getattr(he.response, "status_code", None)
            ) from he
            
        except requests.RequestException as re:
            raise AnkiPHAPIError(f"Network error while downloading deck: {re}") from re
            
        except Exception as e:
            raise AnkiPHAPIError(f"Unexpected error downloading deck: {e}") from e

    # === UPDATE CHECKING (NEW) ===
    
    def check_updates(self) -> Any:
        """
        Check for updates on all purchased decks
        
        Returns:
            {
                "success": true,
                "decks": [
                    {
                        "deck_id": "abc123",
                        "current_version": "1.0.0",
                        "latest_version": "1.2.0",
                        "has_update": true,
                        "update_type": "minor",
                        "changelog_summary": "Added 50 new cards"
                    }
                ]
            }
        """
        return self.post("/addon-check-updates")

    def get_changelog(self, deck_id: str) -> Any:
        """
        Get full changelog/version history for a deck
        
        Args:
            deck_id: The deck ID
        
        Returns:
            {
                "success": true,
                "versions": [
                    {
                        "version": "1.2.0",
                        "released_at": "2024-12-10T10:00:00Z",
                        "changes": ["Added 50 new cards", "Fixed typos"]
                    }
                ]
            }
        """
        return self.post("/addon-get-changelog", json_body={"deck_id": deck_id})

    # === NOTIFICATIONS (NEW) ===
    
    def check_notifications(self, mark_as_read: bool = False, limit: int = 10) -> Any:
        """
        Check for user notifications
        
        Args:
            mark_as_read: Whether to mark notifications as read
            limit: Maximum number of notifications to return
        
        Returns:
            {
                "success": true,
                "notifications": [
                    {
                        "id": "notif123",
                        "type": "deck_update",
                        "title": "Update Available",
                        "message": "Criminal Law v1.5.0 is now available",
                        "created_at": "2024-12-15T08:00:00Z",
                        "read": false
                    }
                ],
                "unread_count": 3
            }
        """
        return self.post(
            "/addon-check-notifications", 
            json_body={"mark_as_read": mark_as_read, "limit": limit}
        )

    # === PROGRESS & SYNC ENDPOINTS ===
    
    def sync_progress(self, progress_data: List[Dict] = None) -> Any:
        """Sync study progress to server"""
        return self.post("/addon-sync-progress", json_body={"progress_data": progress_data or []})

    # === ANKIHUB-PARITY: COLLABORATIVE FEATURES (NEW) ===
    
    def push_changes(self, deck_id: str, changes: List[Dict], version: str) -> Any:
        """
        Push local card edits to server
        
        Args:
            deck_id: The deck ID
            changes: List of card changes
            version: Current deck version
        
        Returns:
            {"success": true, "changes_accepted": 5}
        """
        return self.post("/addon-push-changes", 
                        json_body={"deck_id": deck_id, "changes": changes, "version": version})

    def pull_changes(self, deck_id: str, since: Optional[str] = None, 
                     last_change_id: Optional[str] = None,
                     full_sync: bool = False) -> Any:
        """
        Pull publisher changes since last sync
        
        Args:
            deck_id: The deck ID
            since: ISO 8601 timestamp to pull changes after
            last_change_id: ID of last synced change
            full_sync: If True, returns all cards from collaborative_deck_cards (source of truth)
        
        Returns:
            {
                "success": true,
                "changes": [...],    # if full_sync=False
                "cards": [...],      # if full_sync=True
                "conflicts": [...]
            }
        """
        body = {"deck_id": deck_id, "full_sync": full_sync}
        if since:
            body["since"] = since
        if last_change_id:
            body["last_change_id"] = last_change_id
        
        return self.post("/addon-pull-changes", json_body=body)

    def submit_suggestion(self, deck_id: str, card_guid: str, field_name: str,
                         current_value: str, suggested_value: str, 
                         reason: Optional[str] = None) -> Any:
        """
        Submit a card improvement suggestion
        
        Args:
            deck_id: The deck ID
            card_guid: The card's GUID
            field_name: Name of the field to change
            current_value: Current field value
            suggested_value: Suggested new value
            reason: Optional reason for suggestion
        
        Returns:
            {"success": true, "suggestion_id": "sugg123"}
        """
        return self.post("/addon-submit-suggestion", json_body={
            "deck_id": deck_id,
            "card_guid": card_guid,
            "field_name": field_name,
            "current_value": current_value,
            "suggested_value": suggested_value,
            "reason": reason
        })

    def get_protected_fields(self, deck_id: Optional[str] = None) -> Any:
        """
        Get fields protected from sync overwrites
        
        Args:
            deck_id: Optional deck ID to get specific deck's protected fields
        
        Returns:
            {
                "success": true,
                "protected_fields": ["Personal Notes", "My Tags"]
            }
        """
        body = {"deck_id": deck_id} if deck_id else {}
        return self.post("/addon-protected-fields", json_body=body)

    def set_protected_fields(self, deck_id: str, field_names: List[str]) -> Any:
        """
        Set which fields should be protected from sync overwrites
        
        Args:
            deck_id: The deck ID
            field_names: List of field names to protect
        
        Returns:
            {"success": true}
        """
        return self.post("/addon-protected-fields", 
                        json_body={"deck_id": deck_id, "fields": field_names})

    def get_card_history(self, deck_id: str, card_guid: str, limit: int = 50) -> Any:
        """
        Get change history for a specific card
        
        Args:
            deck_id: The deck ID
            card_guid: The card's GUID
            limit: Maximum number of history entries
        
        Returns:
            {
                "success": true,
                "history": [
                    {
                        "version": "1.2.0",
                        "changed_at": "2024-12-10T10:00:00Z",
                        "changed_by": "publisher",
                        "changes": {"Front": "Old value"}
                    }
                ]
            }
        """
        return self.post("/addon-get-card-history", 
                        json_body={"deck_id": deck_id, "card_guid": card_guid, "limit": limit})

    def rollback_card(self, deck_id: str, card_guid: str, target_version: str) -> Any:
        """
        Rollback a card to a previous version
        
        Args:
            deck_id: The deck ID
            card_guid: The card's GUID
            target_version: Version to rollback to
        
        Returns:
            {"success": true}
        """
        return self.post("/addon-rollback-card", 
                        json_body={
                            "deck_id": deck_id,
                            "card_guid": card_guid,
                            "target_version": target_version
                        })

    # === DATA SYNC (NEW) ===
    
    def sync_tags(self, deck_id: str, action: str, changes: Optional[List] = None, 
                  since: Optional[str] = None) -> Any:
        """
        Sync tags bidirectionally
        
        Args:
            deck_id: The deck ID
            action: 'push' or 'pull'
            changes: List of tag changes (for push)
            since: Timestamp to pull changes after (for pull)
        
        Returns:
            {"success": true, "tags_synced": 10}
        """
        body = {"deck_id": deck_id, "action": action}
        if changes:
            body["changes"] = changes
        if since:
            body["since"] = since
        
        return self.post("/addon-sync-tags", json_body=body)

    def sync_suspend_state(self, deck_id: str, action: str, changes: Optional[List] = None,
                           since: Optional[str] = None) -> Any:
        """
        Sync card suspend/buried state
        
        Args:
            deck_id: The deck ID
            action: 'push' or 'pull'
            changes: List of suspend state changes (for push)
            since: Timestamp to pull changes after (for pull)
        
        Returns:
            {"success": true, "states_synced": 5}
        """
        body = {"deck_id": deck_id, "action": action}
        if changes:
            body["changes"] = changes
        if since:
            body["since"] = since
        
        return self.post("/addon-sync-suspend-state", json_body=body)

    def sync_media(self, deck_id: str, action: str, **kwargs) -> Any:
        """
        Sync media files
        
        Args:
            deck_id: The deck ID
            action: 'list', 'get_upload_url', or 'confirm_upload'
            **kwargs: Additional action-specific parameters
        
        Returns:
            Varies by action
        """
        body = {"deck_id": deck_id, "action": action, **kwargs}
        return self.post("/addon-sync-media", json_body=body)

    def sync_note_types(self, deck_id: str, action: str = "get", 
                        note_types: Optional[List] = None) -> Any:
        """
        Sync note type templates and CSS
        
        Args:
            deck_id: The deck ID
            action: 'get' or 'push'
            note_types: List of note types to push
        
        Returns:
            {"success": true, "note_types": [...]}
        """
        body = {"deck_id": deck_id, "action": action}
        if note_types:
            body["note_types"] = note_types
        
        return self.post("/addon-sync-note-types", json_body=body)

    def pull_changes_full(self, deck_id: str) -> Any:
        """
        Pull full card data from collaborative_deck_cards (source of truth).
        Use for initial sync or complete re-sync.
        
        Args:
            deck_id: The deck ID
        
        Returns:
            {
                "success": true,
                "full_sync": true,
                "cards": [
                    {
                        "card_guid": "abc123",
                        "note_type": "Basic",
                        "fields": {"Front": "...", "Back": "..."},
                        "tags": ["tag1", "tag2"],
                        "updated_at": "2024-12-10T15:00:00Z"
                    }
                ],
                "total_cards": 500,
                "deck_version": "2.1.0"
            }
        """
        return self.post("/addon-pull-changes", json_body={"deck_id": deck_id, "full_sync": True})

    # === ADMIN ENDPOINTS (NEW) ===
    
    def admin_push_changes(self, deck_id: str, changes: List[Dict], version: str,
                           version_notes: Optional[str] = None,
                           timeout: int = 60) -> Any:
        """
        Admin: Push card changes from Anki to database as publisher changes.
        Only available to deck publishers/admins.
        
        Args:
            deck_id: The deck ID
            changes: List of card changes (each with guid, note_type, fields, tags, change_type)
            version: New version string for this update
            version_notes: Optional release notes for this version
            timeout: Request timeout in seconds (default 60)
        
        Returns:
            {"success": true, "cards_added": 0, "cards_modified": 50, "new_version": "2.2.0"}
        """
        body = {"deck_id": deck_id, "changes": changes, "version": version}
        if version_notes:
            body["version_notes"] = version_notes
        return self.post("/addon-admin-push-changes", json_body=body, timeout=timeout)

    def admin_import_deck(self, deck_id: Optional[str], cards: List[Dict], version: str,
                          version_notes: Optional[str] = None,
                          clear_existing: bool = False,
                          deck_title: Optional[str] = None,
                          timeout: int = 60) -> Any:
        """
        Admin: Import full deck to database (initial setup or full refresh).
        Only available to deck publishers/admins.
        
        Args:
            deck_id: The deck ID to import into (None if creating new deck)
            cards: List of card data (each with card_guid, note_type, fields, tags)
            version: Version string for this import
            version_notes: Optional release notes for this version
            clear_existing: If True, clears existing cards before import
            deck_title: Title for new deck (required if deck_id is None)
            timeout: Request timeout in seconds (default 60)
        
        Returns:
            {"success": true, "deck_id": "uuid", "cards_imported": 500, "version": "1.0.0"}
        """
        body = {
            "cards": cards,
            "version": version,
            "clear_existing": clear_existing
        }
        if deck_id:
            body["deck_id"] = deck_id
        if deck_title:
            body["deck_title"] = deck_title
        if version_notes:
            body["version_notes"] = version_notes
        return self.post("/addon-admin-import-deck", json_body=body, timeout=timeout)

    # === COLLABORATIVE DECK MANAGEMENT (v3.0) ===
    
    def create_deck(self, title: str, description: str = "", 
                    bar_subject: Optional[str] = None, 
                    is_public: bool = True,
                    tags: Optional[List[str]] = None) -> Any:
        """
        Create a new collaborative deck (premium users only).
        
        Args:
            title: Deck title (3-100 characters)
            description: Deck description (max 2000 characters)
            bar_subject: Optional bar subject category
            is_public: Whether deck is publicly visible (default True)
            tags: Optional list of tags (max 20, 50 chars each)
        
        Returns:
            {
                "success": true,
                "deck": {
                    "id": "uuid",
                    "title": "My Deck",
                    "description": "...",
                    "bar_subject": "political_law",
                    "is_public": true,
                    "is_verified": false,
                    "card_count": 0,
                    "subscriber_count": 0,
                    "version": "1.0.0",
                    "created_at": "2024-12-18T10:00:00Z"
                }
            }
        
        Errors:
            403: Premium subscription required
            400: Title validation failed
        """
        body = {
            "title": title,
            "description": description,
            "is_public": is_public
        }
        if bar_subject:
            body["bar_subject"] = bar_subject
        if tags:
            body["tags"] = tags
        
        return self.post("/addon-create-deck", json_body=body)

    def update_deck(self, deck_id: str, 
                    title: Optional[str] = None,
                    description: Optional[str] = None,
                    bar_subject: Optional[str] = None,
                    is_public: Optional[bool] = None,
                    tags: Optional[List[str]] = None) -> Any:
        """
        Update metadata for a collaborative deck you created.
        
        Args:
            deck_id: UUID of the deck to update
            title: New title (optional)
            description: New description (optional)
            bar_subject: New bar subject category (optional)
            is_public: Update visibility (optional)
            tags: New tags list (optional)
        
        Returns:
            {"success": true, "deck": {...}}
        
        Errors:
            403: Not authorized (not deck creator)
            404: Deck not found
        """
        body = {"deck_id": deck_id}
        if title is not None:
            body["title"] = title
        if description is not None:
            body["description"] = description
        if bar_subject is not None:
            body["bar_subject"] = bar_subject
        if is_public is not None:
            body["is_public"] = is_public
        if tags is not None:
            body["tags"] = tags
        
        return self.post("/addon-update-deck", json_body=body)

    def delete_user_deck(self, deck_id: str, confirm: bool = False) -> Any:
        """
        Delete a collaborative deck you created.
        
        Args:
            deck_id: UUID of the deck to delete
            confirm: Must be True to confirm deletion
        
        Returns:
            {
                "success": true,
                "message": "Deck deleted successfully",
                "cards_deleted": 150,
                "subscribers_removed": 25
            }
        
        Errors:
            400: Confirmation required (confirm=False)
            403: Not authorized (not deck creator)
            404: Deck not found
        """
        return self.post("/addon-delete-user-deck", 
                        json_body={"deck_id": deck_id, "confirm": confirm})

    def push_deck_cards(self, deck_id: str, cards: List[Dict],
                        delete_missing: bool = False,
                        version: Optional[str] = None,
                        timeout: int = 60) -> Any:
        """
        Push cards from Anki Desktop to your collaborative deck.
        
        Args:
            deck_id: UUID of your collaborative deck
            cards: List of card objects (max 500 per request)
                   Each card: {card_guid, note_type, fields, tags, subdeck_path}
            delete_missing: If True, delete cards not in the provided list
            version: Semantic version (auto-increments if not provided)
            timeout: Request timeout in seconds (default 60)
        
        Returns:
            {
                "success": true,
                "version": "1.0.1",
                "stats": {
                    "cards_processed": 100,
                    "cards_added": 10,
                    "cards_modified": 5,
                    "cards_deleted": 2,
                    "total_cards": 157
                }
            }
        
        Errors:
            400: Too many cards (max 500) or validation errors
            403: Not authorized (not deck creator)
            404: Deck not found
        """
        if len(cards) > 500:
            raise ValueError("Maximum 500 cards per request (per API spec)")
        
        body = {"deck_id": deck_id, "cards": cards}
        if delete_missing:
            body["delete_missing"] = True
        if version:
            body["version"] = version
        
        return self.post("/addon-push-deck-cards", json_body=body, timeout=timeout)

    def get_my_decks(self) -> Any:
        """
        List all collaborative decks created by the authenticated user.
        
        Returns:
            {
                "success": true,
                "decks": [
                    {
                        "id": "uuid",
                        "title": "My Constitutional Law Notes",
                        "description": "...",
                        "bar_subject": "political_law",
                        "card_count": 157,
                        "subscriber_count": 25,
                        "is_public": true,
                        "is_verified": false,
                        "version": "1.0.1",
                        "tags": ["political", "law"],
                        "image_url": "...",
                        "created_at": "2024-12-01T10:00:00Z",
                        "updated_at": "2024-12-18T10:30:00Z"
                    }
                ],
                "can_create_more": true,
                "created_decks_count": 3,
                "max_decks": 10
            }
        """
        return self.post("/addon-get-my-decks", json_body={})


# === GLOBAL INSTANCE ===

# Single shared instance
api = ApiClient()


def set_access_token(token: Optional[str]) -> None:
    """Set the access token for API requests"""
    api.access_token = token
    if token:
        print("✓ Access token set")
    else:
        print("✓ Access token cleared")