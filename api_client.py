"""
Robust API client for Nottorney Add-on
FIXED: Enhanced error handling and response validation
"""

from __future__ import annotations
import json
from typing import Any, Dict, Optional

API_BASE = "https://ladvckxztcleljbiomcf.supabase.co/functions/v1"

try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error
    _HAS_REQUESTS = False


class NottorneyAPIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class ApiClient:
    """API client for Nottorney backend"""
    
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
            raise NottorneyAPIError("Request timed out. Please check your internet connection.")
        except requests.ConnectionError:
            raise NottorneyAPIError("Connection failed. Please check your internet connection.")
        except Exception as e:
            raise NottorneyAPIError(f"Network error: {e}") from e

        # Parse response
        try:
            data = resp.json()
        except Exception: 
            text = resp.text if hasattr(resp, "text") else ""
            raise NottorneyAPIError(
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
            
            raise NottorneyAPIError(err_msg, status_code=resp.status_code, details=data)

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
                    raise NottorneyAPIError(
                        "Invalid JSON response from server", 
                        status_code=resp.getcode(), 
                        details=raw[:500]
                    )
                
                if resp.getcode() >= 400:
                    err_msg = data.get("error") if isinstance(data, dict) else None
                    raise NottorneyAPIError(
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
            
            raise NottorneyAPIError(
                err_msg or f"HTTP {getattr(he, 'code', 'error')}", 
                status_code=getattr(he, "code", None), 
                details=parsed or str(he)
            ) from he
            
        except _urllib_error.URLError as ue:
            raise NottorneyAPIError(f"Connection error: {ue}") from ue
            
        except Exception as e:
            raise NottorneyAPIError(f"Network error: {e}") from e

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

    def browse_decks(self) -> Any:
        """Browse available decks"""
        return self.post("/addon-browse-decks")

    def download_deck(self, deck_id: str) -> Any:
        """Get download URL for a deck"""
        return self.post("/addon-download-deck", json_body={"deck_id": deck_id})

    def batch_download_decks(self, deck_ids: list[str]) -> Any:
        """Download multiple decks"""
        return self.post("/addon-batch-download", json_body={"deck_ids": deck_ids})

    def download_deck_file(self, download_url: str) -> bytes:
        """Download deck file from signed URL"""
        if not download_url:
            raise NottorneyAPIError("Download URL is required")

        if not _HAS_REQUESTS: 
            # Use urllib to fetch bytes
            try:
                req = _urllib_request.Request(download_url, method="GET")
                with _urllib_request.urlopen(req, timeout=120) as resp:
                    content = resp.read()
                    if len(content) == 0:
                        raise NottorneyAPIError("Downloaded file is empty")
                    return content
            except Exception as e:
                raise NottorneyAPIError(f"Network error while downloading deck: {e}") from e

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
                        raise NottorneyAPIError(
                            "Download URL may be expired or invalid. Please try again."
                        )
                except Exception:
                    pass
                raise NottorneyAPIError(
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
                raise NottorneyAPIError("Downloaded file is empty")

            # Quick ZIP signature check (PK magic bytes)
            if len(content) >= 4:
                if content[:2] != b"PK":
                    print("⚠ Warning: downloaded file does not appear to be a ZIP file")
                    # Don't raise error - some .apkg files might have unusual headers

            return bytes(content)
            
        except requests.HTTPError as he:
            raise NottorneyAPIError(
                f"HTTP error while downloading deck: {he}", 
                status_code=getattr(he.response, "status_code", None)
            ) from he
            
        except requests.RequestException as re:
            raise NottorneyAPIError(f"Network error while downloading deck: {re}") from re
            
        except Exception as e:
            raise NottorneyAPIError(f"Unexpected error downloading deck: {e}") from e

    # === PROGRESS & SYNC ENDPOINTS ===
    
    def sync_progress(self, progress_data: list = None) -> Any:
        """Sync study progress to server"""
        return self.post("/addon-sync-progress", json_body={"progress_data": progress_data or []})

    def get_changelog(self, deck_id: str) -> Any:
        """Get changelog for a deck"""
        return self.post("/addon-get-changelog", json_body={"deck_id": deck_id})

    def check_notifications(self, mark_as_read: bool = False, limit: int = 10) -> Any:
        """Check for notifications"""
        return self.post(
            "/addon-check-notifications", 
            json_body={"mark_as_read": mark_as_read, "limit": limit}
        )


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