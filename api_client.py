"""
Robust API client for AnkiPH Add-on
Consolidated and Enhanced Version

Features:
- Thread-safe token refresh with locking
- Exponential backoff with jitter
- Rate limiting support (429 handling)
- Adaptive batch sizing for large datasets
- Comprehensive error handling
- Request/response logging

Version: 4.0.0
"""

from __future__ import annotations
import json
import time
import random
import threading
import webbrowser
from typing import Any, Dict, Optional, List, Callable
from enum import Enum
from datetime import datetime

from .config import config
from .logger import logger

try:
    from .constants import (
        API_BASE_URL,
        API_BATCH_SIZE, API_MAX_BATCH_SIZE, API_MIN_BATCH_SIZE,
        SYNC_TIMEOUT_SECONDS, DOWNLOAD_TIMEOUT_SECONDS,
        TARGET_REQUEST_DURATION_MIN, TARGET_REQUEST_DURATION_MAX,
        DEFAULT_MAX_RETRIES, MIN_TOKEN_LENGTH,
        PREMIUM_URL
    )
except ImportError:
    # Fallback constants if constants.py is missing
    API_BASE_URL = "https://ladvckxztcleljbiomcf.supabase.co/functions/v1"
    PREMIUM_URL = "https://ankiph.lovable.app/subscription"
    API_BATCH_SIZE = 500
    API_MAX_BATCH_SIZE = 1000
    API_MIN_BATCH_SIZE = 200
    SYNC_TIMEOUT_SECONDS = 30
    DOWNLOAD_TIMEOUT_SECONDS = 120
    TARGET_REQUEST_DURATION_MIN = 2.0
    TARGET_REQUEST_DURATION_MAX = 5.0
    DEFAULT_MAX_RETRIES = 3
    MIN_TOKEN_LENGTH = 20

# API Configuration
API_VERSION = "4.0"

# HTTP Library Detection
try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except ImportError:
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error
    _HAS_REQUESTS = False


# ============================================================================
# ACCESS CONTROL SYSTEM (v4.0)
# ============================================================================

class AccessTier(Enum):
    """User access tier for AnkiPH (v4.0 unified hierarchy)"""
    ADMIN = "admin"
    COLLECTION_OWNER = "collection_owner"
    SUBSCRIBER = "subscriber"
    DECK_SUBSCRIBER = "deck_subscriber"
    LEGACY_PURCHASE = "legacy_purchase"
    FREE_TIER = "free_tier"
    PUBLIC_DECK = "public_deck"


def check_access(user_data: dict, deck: dict) -> Optional[AccessTier]:
    """
    Determine user's access tier for a specific deck.
    
    Priority hierarchy:
    1. Admin (highest)
    2. Collection Owner (₱1000 lifetime)
    3. Active Subscriber
    4. Deck Subscriber
    5. Legacy Purchase
    6. Free Tier / Public Deck (lowest)
    
    Args:
        user_data: Dict with is_admin, owns_collection, has_subscription
        deck: Dict with access_type field from API response
    
    Returns:
        AccessTier enum value, or None if no access
    """
    # Priority 1: Admin
    if user_data.get("is_admin"):
        return AccessTier.ADMIN
    
    # Priority 2: Collection owner
    if user_data.get("owns_collection"):
        return AccessTier.COLLECTION_OWNER
    
    # Priority 3: Active premium subscription
    if user_data.get("has_subscription"):
        expires = user_data.get("subscription_expires_at")
        if expires:
            try:
                expiry = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                if expiry > datetime.now(expiry.tzinfo):
                    return AccessTier.SUBSCRIBER
            except (ValueError, TypeError):
                # If we can't parse, assume valid
                return AccessTier.SUBSCRIBER
        else:
            # No expiry means lifetime
            return AccessTier.SUBSCRIBER
    
    # Priority 4-7: Deck-level access
    access_type = deck.get("access_type", "")
    if access_type == "deck_subscriber":
        return AccessTier.DECK_SUBSCRIBER
    if access_type == "legacy_purchase":
        return AccessTier.LEGACY_PURCHASE
    if access_type == "free_tier":
        return AccessTier.FREE_TIER
    if access_type == "public_deck":
        return AccessTier.PUBLIC_DECK
    
    return None


def can_sync_updates(tier: Optional[AccessTier]) -> bool:
    """
    Check if user's tier allows syncing updates.
    Free tier and public deck users cannot sync.
    
    Args:
        tier: The user's AccessTier
    
    Returns:
        True if user can sync updates
    """
    if tier is None:
        return False
    return tier in [
        AccessTier.ADMIN,
        AccessTier.COLLECTION_OWNER,
        AccessTier.SUBSCRIBER,
        AccessTier.DECK_SUBSCRIBER,
        AccessTier.LEGACY_PURCHASE
    ]


def show_upgrade_prompt():
    """
    Show upgrade dialog when user tries to access paid content.
    Opens browser to subscription page.
    """
    try:
        from aqt.qt import QMessageBox
        from aqt import mw
        
        dialog = QMessageBox(mw)
        dialog.setWindowTitle("Subscription Required")
        dialog.setText(
            "This deck requires an AnkiPH subscription.\n\n"
            "• Student: ₱100/month\n"
            "• Regular: ₱149/month\n\n"
            "Subscribe to sync all 33,709+ Philippine bar exam cards."
        )
        dialog.setIcon(QMessageBox.Icon.Information)
        
        subscribe_btn = dialog.addButton("Subscribe Now", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        dialog.exec()
        
        if dialog.clickedButton() == subscribe_btn:
            webbrowser.open(PREMIUM_URL)
    except Exception as e:
        logger.error(f"Failed to show upgrade prompt: {e}")


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class AnkiPHAPIError(Exception):
    """Base exception for all API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details
    
    def is_auth_error(self) -> bool:
        """Check if this is an authentication error"""
        return self.status_code in (401, 403)
    
    def is_server_error(self) -> bool:
        """Check if this is a server error (5xx)"""
        return self.status_code and 500 <= self.status_code < 600


class AnkiPHRateLimitError(AnkiPHAPIError):
    """Exception for API rate limiting (429)"""
    def __init__(self, message: str, retry_after: int, details: Optional[Any] = None):
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after


# ============================================================================
# API CLIENT
# ============================================================================

class ApiClient:
    """
    Thread-safe API client for AnkiPH backend.
    
    Features:
    - Automatic token refresh on 401
    - Exponential backoff with jitter
    - Rate limiting support
    - Request/response logging
    - Adaptive batch sizing
    """
    
    def __init__(self, access_token: Optional[str] = None, base_url: str = API_BASE_URL):
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self._refresh_lock = threading.Lock()  # Thread-safe token refresh
        self._refresh_attempted = False  # Track if refresh was attempted this session

    # ------------------------------------------------------------------------
    # Core HTTP Methods
    # ------------------------------------------------------------------------

    def _headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Build request headers with optional authentication"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Version": API_VERSION
        }
        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _full_url(self, path: str) -> str:
        """
        Build full URL from path with validation.
        
        Raises:
            ValueError: If path is empty or invalid
        """
        if not path:
            raise ValueError("API path cannot be empty")
        
        clean_path = path.lstrip('/')
        if not clean_path:
            raise ValueError("API path cannot be just a slash")
        
        return f"{self.base_url}/{clean_path}"

    def post(
        self, 
        path: str, 
        json_body: Optional[Dict[str, Any]] = None, 
        require_auth: bool = True, 
        timeout: int = SYNC_TIMEOUT_SECONDS, 
        max_retries: int = DEFAULT_MAX_RETRIES
    ) -> Any:
        """
        Make POST request with comprehensive retry logic and token refresh.
        
        Args:
            path: API endpoint path (e.g., "/addon-login")
            json_body: JSON request body
            require_auth: Whether to include auth token
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts (excluding initial try)
        
        Returns:
            Parsed JSON response
        
        Raises:
            AnkiPHAPIError: On API errors
            AnkiPHRateLimitError: On rate limiting (429)
        """
        url = self._full_url(path)
        
        # Reset refresh flag for each new request (allows retry on new 401s)
        self._refresh_attempted = False
        
        # Log request (debug level)
        logger.debug(
            f"POST {path} "
            f"(auth={require_auth}, timeout={timeout}s, "
            f"body_keys={list(json_body.keys()) if json_body else 'None'})"
        )
        
        for attempt in range(max_retries + 1):
            try:
                headers = self._headers(include_auth=require_auth)
                
                # Make request
                start_time = time.time()
                if _HAS_REQUESTS:
                    result = self._post_with_requests(url, headers, json_body, timeout)
                else:
                    result = self._post_with_urllib(url, headers, json_body, timeout)
                
                # Log success
                duration = time.time() - start_time
                logger.debug(f"POST {path} succeeded in {duration:.2f}s")
                
                return result
                    
            except AnkiPHRateLimitError as e:
                # Rate limiting - wait and retry
                if attempt == max_retries:
                    logger.error(f"Rate limited after {max_retries} retries: {e}")
                    raise
                
                wait_time = e.retry_after
                logger.warning(
                    f"Rate limited on {path}. "
                    f"Waiting {wait_time}s (attempt {attempt+1}/{max_retries})"
                )
                time.sleep(wait_time)
                continue
                
            except AnkiPHAPIError as e:
                # Handle 401 - attempt token refresh (once per request)
                if e.status_code == 401 and require_auth and not self._refresh_attempted:
                    if self._try_refresh_token():
                        logger.info(f"Token refreshed, retrying {path}")
                        self._refresh_attempted = True
                        continue  # Retry with new token
                
                # Don't retry auth errors
                if e.is_auth_error():
                    logger.error(f"Authentication error on {path}: {e}")
                    config.clear_tokens()
                    self.access_token = None
                    raise
                
                # Retry server errors with exponential backoff
                if e.is_server_error() and attempt < max_retries:
                    wait_time = (2 ** attempt) + random.random()
                    logger.warning(
                        f"Server error {e.status_code} on {path}. "
                        f"Retrying in {wait_time:.1f}s... (attempt {attempt+1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue
                
                # Other errors - don't retry
                logger.error(f"API error on {path}: {e}")
                raise
                
            except Exception as e:
                # Network/connection errors - retry with backoff
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + random.random()
                    logger.warning(
                        f"Network error on {path}: {e}. "
                        f"Retrying in {wait_time:.1f}s... (attempt {attempt+1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Network error on {path} after {max_retries} retries: {e}")
                    raise

    def _try_refresh_token(self) -> bool:
        """
        Thread-safe token refresh with expiry check.
        
        Returns:
            True if token was successfully refreshed
        """
        with self._refresh_lock:
            # Check if another thread already refreshed
            if self._refresh_attempted:
                logger.debug("Token already refreshed by another thread")
                return True
            
            try:
                refresh_token = config.get_refresh_token()
                if not refresh_token:
                    logger.warning("No refresh token available")
                    return False
                
                # Check if token is actually expired (avoid unnecessary refresh)
                expires_at = config.get_token_expiry()
                if expires_at and not check_token_expiry(expires_at):
                    logger.debug("Token still valid, skipping refresh")
                    return True
                
                logger.info("Refreshing expired access token...")
                new_tokens = self.refresh_access_token(refresh_token)
                
                if new_tokens and new_tokens.get("access_token"):
                    self.access_token = new_tokens["access_token"]
                    new_refresh = new_tokens.get("refresh_token") or refresh_token
                    new_expires = new_tokens.get("expires_at")
                    config.save_tokens(self.access_token, new_refresh, new_expires)
                    logger.info("✓ Token refreshed successfully")
                    self._refresh_attempted = True
                    return True
                
                logger.error("Token refresh returned no access token")
                return False
                    
            except Exception as e:
                logger.error(f"Token refresh failed: {e}", exc_info=True)
                return False

    def _parse_response(self, response, is_error_response: bool = False) -> Any:
        """
        Parse and validate HTTP response (shared logic).
        
        Args:
            response: requests.Response or http.client.HTTPResponse object
            is_error_response: True if this is being called from error handler
        
        Returns:
            Parsed JSON data
        
        Raises:
            AnkiPHAPIError: On parsing errors or HTTP errors
            AnkiPHRateLimitError: On 429 rate limiting
        """
        # Parse JSON
        try:
            if hasattr(response, 'json'):
                data = response.json()
            else:
                content = response.read() if hasattr(response, 'read') else b''
                data = json.loads(content.decode("utf-8"))
        except Exception as e:
            status = response.status_code if hasattr(response, 'status_code') else response.getcode()
            raise AnkiPHAPIError(
                f"Invalid JSON response from server (HTTP {status})", 
                status_code=status,
                details=str(e)
            )
        
        status = response.status_code if hasattr(response, 'status_code') else (response.code if hasattr(response, 'code') else response.getcode())
        
        # Check for rate limiting (429)
        if status == 429:
            retry_after = 60  # Default
            try:
                retry_after = int(response.headers.get('Retry-After', 60))
            except (ValueError, TypeError, AttributeError):
                pass
            
            err_msg = data.get("error", "Rate limit exceeded") if isinstance(data, dict) else "Rate limit exceeded"
            raise AnkiPHRateLimitError(
                f"{err_msg}. Retry in {retry_after} seconds.", 
                retry_after=retry_after,
                details=data
            )
        
        # Check for HTTP errors (4xx, 5xx)
        if status >= 400:
            err_msg = None
            if isinstance(data, dict):
                err_msg = data.get("error") or data.get("message") or data.get("detail")
            
            raise AnkiPHAPIError(
                err_msg or f"HTTP {status} error", 
                status_code=status, 
                details=data
            )
        
        return data

    def _post_with_requests(
        self, 
        url: str, 
        headers: Dict[str, str], 
        json_body: Optional[Dict[str, Any]], 
        timeout: int
    ) -> Any:
        """POST using requests library (preferred)"""
        resp = requests.post(url, headers=headers, json=json_body or {}, timeout=timeout)
        return self._parse_response(resp)

    def _post_with_urllib(
        self, 
        url: str, 
        headers: Dict[str, str], 
        json_body: Optional[Dict[str, Any]], 
        timeout: int
    ) -> Any:
        """POST using urllib (fallback when requests not available)"""
        try:
            req_data = json.dumps(json_body or {}).encode("utf-8")
            req = _urllib_request.Request(url, data=req_data, headers=headers, method="POST")
            
            resp = _urllib_request.urlopen(req, timeout=timeout)
            return self._parse_response(resp)
                
        except _urllib_error.HTTPError as he:
            # FIXED: Handle 429 and other HTTP errors properly in error handler
            return self._parse_response(he, is_error_response=True)
            
        except _urllib_error.URLError as ue:
            raise AnkiPHAPIError(
                f"Connection error: {ue}\n\n"
                f"Troubleshooting:\n"
                f"• Check your internet connection\n"
                f"• Verify the API URL: {self.base_url}\n"
                f"• Check firewall settings"
            ) from ue

    # ------------------------------------------------------------------------
    # Authentication Endpoints
    # ------------------------------------------------------------------------
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login with email and password.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            {
                "success": true,
                "access_token": "...",
                "refresh_token": "...",
                "user": {...}
            }
        """
        return self.post(
            "/addon-login", 
            json_body={"email": email, "password": password}, 
            require_auth=False
        )

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            {
                "success": true,
                "access_token": "...",
                "refresh_token": "..."
            }
        """
        return self.post(
            "/addon-refresh-token", 
            json_body={"refresh_token": refresh_token}, 
            require_auth=False
        )

    # ------------------------------------------------------------------------
    # Deck Endpoints
    # ------------------------------------------------------------------------
    
    def browse_decks(
        self, 
        category: str = "all", 
        search: Optional[str] = None,
        page: int = 1, 
        limit: int = 20
    ) -> Any:
        """
        Browse available decks with filtering.
        
        Args:
            category: "all" | "featured" | "community" | "subscribed"
            search: Optional search term
            page: Page number (default: 1)
            limit: Results per page (default: 20, max: 100)
        
        Returns:
            {
                "success": true,
                "decks": [...],
                "total": 45,
                "page": 1,
                "total_pages": 3
            }
        """
        json_body = {
            "action": "list",
            "category": category,
            "page": page,
            "limit": min(limit, 100)
        }
        if search:
            json_body["search"] = search
        
        return self.post("/addon-browse-decks", json_body=json_body)

    def download_deck(self, deck_id: str, include_media: bool = True) -> Any:
        """
        Download full deck content (initial sync).
        
        Args:
            deck_id: The deck UUID
            include_media: Whether to include media files (default: True)
        
        Returns:
            {
                "success": true,
                "deck": {...},
                "cards": [...],
                "note_types": [...],
                "media_files": [...]
            }
        """
        return self.post("/addon-download-deck", json_body={
            "deck_id": deck_id,
            "include_media": include_media
        })

    def check_updates(self) -> Any:
        """
        Check for deck updates (global check for all subscribed decks).
        
        Returns:
            {
                "success": true,
                "decks": [
                    {
                        "deck_id": "...",
                        "has_update": true,
                        "current_version": "1.0.0",
                        "synced_version": "0.9.0"
                    }
                ]
            }
        """
        return self.post("/addon-check-updates", json_body={})

    def manage_subscription(
        self, 
        action: str, 
        deck_id: str,
        sync_enabled: bool = True,
        notify_updates: bool = True
    ) -> Any:
        """
        Manage deck subscriptions.
        
        Args:
            action: "subscribe" | "unsubscribe" | "update" | "get"
            deck_id: The deck UUID
            sync_enabled: Enable auto-sync for this deck
            notify_updates: Receive update notifications
        
        Returns:
            Depends on action:
            - subscribe/unsubscribe: {"success": true, "subscribed": bool}
            - update: {"success": true}
            - get: {"success": true, "subscription": {...}}
        """
        json_body = {"action": action, "deck_id": deck_id}
        if action in ("subscribe", "update"):
            json_body["sync_enabled"] = sync_enabled
            json_body["notify_updates"] = notify_updates
        
        return self.post("/addon-manage-subscription", json_body=json_body)

    def get_changelog(self, deck_id: str, from_version: Optional[str] = None) -> Any:
        """
        Get changelog/version history for a deck.
        
        Args:
            deck_id: The deck UUID
            from_version: Optional version to get changes after
        
        Returns:
            {
                "success": true,
                "changelog": [
                    {
                        "version": "1.0.1",
                        "notes": "...",
                        "cards_added": 10,
                        "released_at": "..."
                    }
                ]
            }
        """
        json_body = {"deck_id": deck_id}
        if from_version:
            json_body["from_version"] = from_version
        return self.post("/addon-get-changelog", json_body=json_body)

    def check_notifications(self, last_check: Optional[str] = None) -> Any:
        """
        Check for pending notifications.
        
        Args:
            last_check: ISO 8601 timestamp of last check
        
        Returns:
            {
                "success": true,
                "notifications": [
                    {
                        "id": "...",
                        "type": "deck_update",
                        "title": "...",
                        "message": "..."
                    }
                ]
            }
        """
        json_body = {}
        if last_check:
            json_body["last_check"] = last_check
        return self.post("/addon-check-notifications", json_body=json_body)

    # ------------------------------------------------------------------------
    # Progress & Sync Endpoints
    # ------------------------------------------------------------------------
    
    def sync_progress(
        self, 
        deck_id: str = None, 
        progress: Dict = None,
        progress_data: List[Dict] = None
    ) -> Any:
        """
        Sync study progress to server (v4.0 format).
        
        Args:
            deck_id: The deck UUID (for single-deck sync)
            progress: Progress data dict (for single-deck sync)
            progress_data: List of progress entries (batch format)
        
        Returns:
            {"success": true, "synced_at": "...", "leaderboard_updated": true}
        """
        if deck_id and progress:
            # Single deck format
            progress_entry = {"deck_id": deck_id, **progress}
            return self.post("/addon-sync-progress", json_body={
                "progress": [progress_entry]
            })
        elif progress_data:
            # Batch format
            return self.post("/addon-sync-progress", json_body={
                "progress": progress_data
            })
        else:
            # Empty sync
            return self.post("/addon-sync-progress", json_body={
                "progress": []
            })

    # ------------------------------------------------------------------------
    # Collaborative Features
    # ------------------------------------------------------------------------
    
    def push_changes(self, deck_id: str, changes: List[Dict]) -> Any:
        """
        Push user's local changes as suggestions for review.
        
        Args:
            deck_id: The deck UUID
            changes: List of card changes with card_guid, field_name, old_value, new_value
        
        Returns:
            {"success": true, "changes_saved": 1}
        """
        return self.post("/addon-push-changes", json_body={
            "deck_id": deck_id,
            "changes": changes
        })

    def pull_changes(
        self, 
        deck_id: str, 
        since: Optional[str] = None, 
        last_change_id: Optional[str] = None,
        full_sync: bool = False, 
        offset: int = 0,
        limit: int = API_BATCH_SIZE
    ) -> Any:
        """
        Pull publisher changes since last sync.
        
        Args:
            deck_id: The deck UUID
            since: ISO 8601 timestamp to pull changes after
            last_change_id: ID of last synced change
            full_sync: If True, returns all cards (initial sync)
            offset: Pagination offset for full_sync
            limit: Number of cards per page (max 1000)
        
        Returns:
            Incremental sync:
            {
                "success": true,
                "changes": [...],
                "latest_change_id": "..."
            }
            
            Full sync:
            {
                "success": true,
                "cards": [...],
                "note_types": [...],
                "total_cards": 32435,
                "has_more": true,
                "next_offset": 1000
            }
        """
        body = {
            "deck_id": deck_id, 
            "full_sync": full_sync,
            "offset": offset,
            "limit": limit
        }
        if since:
            body["since"] = since
        if last_change_id:
            body["last_change_id"] = last_change_id
        
        return self.post("/addon-pull-changes", json_body=body)
    
    def pull_all_cards(
        self, 
        deck_id: str, 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> dict:
        """
        Pull ALL cards from a deck with automatic pagination.
        
        This method handles large decks (32,000+ cards) by:
        - Fetching in batches to avoid timeouts
        - Adaptive batch sizing based on network speed
        - Progress callbacks for UI updates
        
        Args:
            deck_id: The deck UUID
            progress_callback: Optional function(fetched: int, total: int) -> None
        
        Returns:
            {
                "success": true,
                "cards": [...],  # All cards combined
                "note_types": [...],
                "total_cards": 32435,
                "latest_change_id": "..."
            }
        """
        all_cards = []
        note_types = []
        latest_change_id = None
        total_cards = 0
        offset = 0
        limit = API_BATCH_SIZE  # Initial batch size
        
        while True:
            start_time = time.time()
            
            result = self.pull_changes(
                deck_id=deck_id,
                full_sync=True,
                offset=offset,
                limit=limit
            )
            
            duration = time.time() - start_time
            
            if not result.get('success'):
                return result  # Return error
            
            cards = result.get('cards', [])
            
            # Adaptive batch sizing based on request duration
            if len(cards) >= limit:
                if duration > TARGET_REQUEST_DURATION_MAX and limit > API_MIN_BATCH_SIZE:
                    # Too slow, reduce batch size
                    limit = max(API_MIN_BATCH_SIZE, int(limit * 0.85))
                    logger.debug(f"Reducing batch size to {limit} (slow connection)")
                elif duration < TARGET_REQUEST_DURATION_MIN and limit < API_MAX_BATCH_SIZE:
                    # Fast enough, increase batch size
                    limit = min(API_MAX_BATCH_SIZE, int(limit * 1.3))
                    logger.debug(f"Increasing batch size to {limit} (fast connection)")
            
            all_cards.extend(cards)
            
            # Get metadata from first batch only
            if offset == 0:
                note_types = result.get('note_types', [])
                total_cards = result.get('total_cards', len(cards))
                latest_change_id = result.get('latest_change_id')
            
            # Progress callback
            if progress_callback:
                try:
                    progress_callback(len(all_cards), total_cards)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            logger.info(
                f"Fetched batch: offset={offset}, got {len(cards)} cards "
                f"(total: {len(all_cards)}/{total_cards})"
            )
            
            # Check if more to fetch
            has_more = result.get('has_more', len(cards) == limit)
            if not has_more or len(cards) == 0:
                break
            
            # Move to next page
            offset = result.get('next_offset', offset + limit)
        
        logger.info(f"Pull complete: fetched {len(all_cards)} cards in total")
        
        return {
            "success": True,
            "cards": all_cards,
            "note_types": note_types,
            "total_cards": len(all_cards),
            "latest_change_id": latest_change_id
        }

    def submit_suggestion(
        self, 
        deck_id: str, 
        card_guid: str, 
        field_name: str,
        current_value: str, 
        suggested_value: str, 
        reason: Optional[str] = None
    ) -> Any:
        """
        Submit a card improvement suggestion.
        
        Args:
            deck_id: The deck UUID
            card_guid: The card's GUID
            field_name: Name of the field to change
            current_value: Current field value
            suggested_value: Suggested new value
            reason: Optional reason for suggestion
        
        Returns:
            {"success": true, "suggestion_id": "..."}
        """
        return self.post("/addon-submit-suggestion", json_body={
            "deck_id": deck_id,
            "card_guid": card_guid,
            "field_name": field_name,
            "current_value": current_value,
            "suggested_value": suggested_value,
            "reason": reason
        })

    def get_protected_fields(self, deck_id: str) -> Any:
        """
        Get user's protected fields (won't be overwritten during sync).
        
        Args:
            deck_id: The deck UUID
        
        Returns:
            {
                "success": true,
                "protected_fields": [
                    {
                        "card_guid": "...",
                        "field_names": ["Extra", "Personal Notes"]
                    }
                ]
            }
        """
        return self.post("/addon-get-protected-fields", json_body={"deck_id": deck_id})

    def get_card_history(self, deck_id: str, card_guid: str, limit: int = 50) -> Any:
        """
        Get change history for a specific card.
        
        Args:
            deck_id: The deck UUID
            card_guid: The card's GUID
            limit: Maximum number of history entries
        
        Returns:
            {
                "success": true,
                "history": [
                    {
                        "version": "1.2.0",
                        "changed_at": "...",
                        "changed_by": "...",
                        "changes": {...}
                    }
                ]
            }
        """
        return self.post("/addon-get-card-history", json_body={
            "deck_id": deck_id,
            "card_guid": card_guid,
            "limit": limit
        })

    def rollback_card(self, deck_id: str, card_guid: str, target_version: str) -> Any:
        """
        Rollback a card to a previous version.
        
        Args:
            deck_id: The deck UUID
            card_guid: The card's GUID
            target_version: Version to rollback to
        
        Returns:
            {"success": true}
        """
        return self.post("/addon-rollback-card", json_body={
            "deck_id": deck_id,
            "card_guid": card_guid,
            "target_version": target_version
        })

    # ------------------------------------------------------------------------
    # Data Sync (Advanced)
    # ------------------------------------------------------------------------
    
    def sync_tags(
        self, 
        deck_id: str, 
        action: str = "pull", 
        tags: Optional[List[Dict]] = None
    ) -> Any:
        """
        Sync card tags.
        
        Args:
            deck_id: The deck UUID
            action: "pull" or "push"
            tags: List of tag entries for push [{"card_guid": "...", "tags": [...]}]
        
        Returns:
            {"success": true, "tags_added": 0, "tags_removed": 0}
        """
        json_body = {"deck_id": deck_id, "action": action}
        if tags:
            json_body["tags"] = tags
        return self.post("/addon-sync-tags", json_body=json_body)

    def sync_suspend_state(
        self, 
        deck_id: str, 
        action: str = "pull", 
        states: Optional[List[Dict]] = None
    ) -> Any:
        """
        Sync card suspend/bury states.
        
        Args:
            deck_id: The deck UUID
            action: "pull" or "push"
            states: List of states for push [{"card_guid": "...", "is_suspended": bool}]
        
        Returns:
            {"success": true, "cards_updated": 0}
        """
        json_body = {"deck_id": deck_id, "action": action}
        if states:
            json_body["states"] = states
        return self.post("/addon-sync-suspend-state", json_body=json_body)

    def sync_media(
        self, 
        deck_id: str, 
        action: str, 
        file_hashes: Optional[List[str]] = None,
        files: Optional[List[Dict]] = None
    ) -> Any:
        """
        Sync media files.
        
        Args:
            deck_id: The deck UUID
            action: "check" | "upload" | "download"
            file_hashes: List of file hashes to check
            files: List of files to upload [{"file_name": "...", "content_base64": "..."}]
        
        Returns:
            For check:
                {"success": true, "missing_files": [...], "files_to_download": [...]}
            For upload/download:
                {"success": true, "files_uploaded": 0, "files_downloaded": 0}
        """
        json_body = {"deck_id": deck_id, "action": action}
        if file_hashes:
            json_body["file_hashes"] = file_hashes
        if files:
            json_body["files"] = files
        return self.post("/addon-sync-media", json_body=json_body)

    def sync_note_types(
        self, 
        deck_id: str, 
        action: str = "get", 
        note_types: Optional[List] = None
    ) -> Any:
        """
        Sync note type templates and CSS.
        
        Args:
            deck_id: The deck UUID
            action: 'get' or 'push'
            note_types: List of note types to push
        
        Returns:
            {"success": true, "note_types": [...], "types_updated": 0}
        """
        body = {"deck_id": deck_id, "action": action}
        if note_types:
            body["note_types"] = note_types
        
        return self.post("/addon-sync-note-types", json_body=body)

    # ------------------------------------------------------------------------
    # Admin Endpoints
    # ------------------------------------------------------------------------

    def admin_push_changes(
        self, 
        deck_id: str, 
        changes: List[Dict], 
        version: str,
        version_notes: Optional[str] = None,
        timeout: int = 120
    ) -> Any:
        """
        Admin: Push card changes from Anki to database as publisher changes.
        
        Args:
            deck_id: The deck UUID
            changes: List of card changes
            version: New version string
            version_notes: Optional release notes
            timeout: Request timeout (default 120s for large batches)
        
        Returns:
            {"success": true, "cards_added": 0, "cards_modified": 50, "new_version": "..."}
        """
        body = {"deck_id": deck_id, "changes": changes, "version": version}
        if version_notes:
            body["version_notes"] = version_notes
        return self.post("/addon-admin-push-changes", json_body=body, timeout=timeout)

    def admin_import_deck(
        self, 
        deck_id: Optional[str], 
        cards: List[Dict], 
        version: str,
        version_notes: Optional[str] = None,
        clear_existing: bool = False,
        deck_title: Optional[str] = None,
        timeout: int = 180
    ) -> Any:
        """
        Admin: Import full deck to database (initial setup or full refresh).
        
        Args:
            deck_id: The deck UUID (None if creating new deck)
            cards: List of card data
            version: Version string
            version_notes: Optional release notes
            clear_existing: If True, clears existing cards before import
            deck_title: Title for new deck (required if deck_id is None)
            timeout: Request timeout (default 180s for large imports)
        
        Returns:
            {"success": true, "deck_id": "...", "cards_imported": 500, "version": "..."}
        """
        body = {"cards": cards, "version": version, "clear_existing": clear_existing}
        if deck_id:
            body["deck_id"] = deck_id
        if deck_title:
            body["deck_title"] = deck_title
        if version_notes:
            body["version_notes"] = version_notes
        return self.post("/addon-admin-import-deck", json_body=body, timeout=timeout)

    # ------------------------------------------------------------------------
    # Collaborative Deck Management (User-Created Decks)
    # ------------------------------------------------------------------------
    
    def create_deck(
        self, 
        title: str, 
        description: str = "", 
        bar_subject: Optional[str] = None, 
        is_public: bool = True,
        tags: Optional[List[str]] = None
    ) -> Any:
        """
        Create a new collaborative deck (premium users only).
        
        Args:
            title: Deck title (3-100 characters)
            description: Deck description (max 2000 characters)
            bar_subject: Optional bar subject category
            is_public: Whether deck is publicly visible
            tags: Optional list of tags (max 20, 50 chars each)
        
        Returns:
            {"success": true, "deck": {...}}
        """
        body = {"title": title, "description": description, "is_public": is_public}
        if bar_subject:
            body["bar_subject"] = bar_subject
        if tags:
            body["tags"] = tags
        
        return self.post("/addon-create-deck", json_body=body)

    def update_deck(
        self, 
        deck_id: str, 
        title: Optional[str] = None,
        description: Optional[str] = None,
        bar_subject: Optional[str] = None,
        is_public: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> Any:
        """
        Update metadata for a collaborative deck you created.
        
        Args:
            deck_id: UUID of the deck to update
            title: New title (optional)
            description: New description (optional)
            bar_subject: New bar subject (optional)
            is_public: Update visibility (optional)
            tags: New tags list (optional)
        
        Returns:
            {"success": true, "deck": {...}}
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
            {"success": true, "cards_deleted": 150, "subscribers_removed": 25}
        """
        return self.post("/addon-delete-user-deck", json_body={
            "deck_id": deck_id,
            "confirm": confirm
        })

    def push_deck_cards(
        self, 
        deck_id: str, 
        cards: List[Dict],
        delete_missing: bool = False,
        version: Optional[str] = None,
        timeout: int = 120
    ) -> Any:
        """
        Push cards from Anki to your collaborative deck.
        
        Args:
            deck_id: UUID of your collaborative deck
            cards: List of card objects (max 500 per request)
            delete_missing: If True, delete cards not in provided list
            version: Semantic version (auto-increments if not provided)
            timeout: Request timeout (default 120s)
        
        Returns:
            {
                "success": true,
                "version": "1.0.1",
                "stats": {"cards_added": 10, "cards_modified": 5, ...}
            }
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
                "decks": [...],
                "can_create_more": true,
                "created_decks_count": 3,
                "max_decks": 10
            }
        """
        return self.post("/addon-get-my-decks", json_body={})


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_token_expiry(expires_at) -> bool:
    """
    Check if a token has expired.
    
    Args:
        expires_at: Unix timestamp (int/str) or ISO format timestamp string
    
    Returns:
        True if token is expired, False if still valid
    """
    if not expires_at:
        return False  # No expiry = assume valid
    
    try:
        # Handle Unix timestamp (integer or numeric string)
        if isinstance(expires_at, (int, float)):
            expiry = datetime.fromtimestamp(expires_at)
            return datetime.now() >= expiry
        
        # Try parsing as numeric string (Unix timestamp)
        if isinstance(expires_at, str) and expires_at.isdigit():
            expiry = datetime.fromtimestamp(int(expires_at))
            return datetime.now() >= expiry
        
        # Try parsing as ISO format string
        if isinstance(expires_at, str):
            expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            now = datetime.now(expiry.tzinfo)
            return now >= expiry
        
        return False  # Unknown format, assume valid
        
    except (ValueError, TypeError, AttributeError, OSError) as e:
        logger.warning(f"Could not parse token expiry '{expires_at}': {e}")
        return False  # Assume valid if can't parse


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Single shared API client instance
api = ApiClient()


def set_access_token(token: Optional[str]) -> None:
    """
    Set the access token for API requests with validation.
    
    Args:
        token: Access token string or None to clear
    
    Raises:
        ValueError: If token format is invalid
    """
    if token:
        # Validate token format
        if not isinstance(token, str):
            raise ValueError("Token must be a string")
        
        if len(token) < MIN_TOKEN_LENGTH:
            raise ValueError(f"Token too short (minimum {MIN_TOKEN_LENGTH} characters)")
        
        api.access_token = token
        # Secure logging (don't log full token)
        masked = f"{token[:4]}...{token[-4:]}" if len(token) > 10 else "***"
        logger.info(f"✓ Access token set ({masked})")
    else:
        api.access_token = None
        logger.info("✓ Access token cleared")


def ensure_valid_token() -> bool:
    """
    Ensure we have a valid access token, refreshing if needed.
    
    Returns:
        True if we have a valid token (existing or refreshed)
    """
    token = config.get_access_token()
    if not token:
        set_access_token(None)
        return False
    
    # Check expiry
    expires_at = config.get_token_expiry()
    if not check_token_expiry(expires_at):
        # Token still valid
        set_access_token(token)
        return True
    
    # Token expired - try refresh
    refresh_token = config.get_refresh_token()
    if not refresh_token:
        logger.warning("Token expired and no refresh token available")
        return False
    
    try:
        logger.info("Access token expired, attempting refresh...")
        result = api.refresh_access_token(refresh_token)
        
        if result.get('success'):
            new_token = result.get('access_token')
            new_refresh = result.get('refresh_token', refresh_token)
            new_expires = result.get('expires_at')
            
            if new_token:
                config.save_tokens(new_token, new_refresh, new_expires)
                set_access_token(new_token)
                logger.info("✓ Token refreshed successfully")
                return True
        
        logger.error("Token refresh failed: no access token in response")
        return False
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        return False