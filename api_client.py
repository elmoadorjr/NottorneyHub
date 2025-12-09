"""
API client for the Nottorney backend
Handles all HTTP requests to your API
"""

import requests
from typing import Dict, List, Optional
from .config import config


class NottorneyAPIError(Exception):
    """Custom exception for API errors"""
    pass


class NottorneyAPI:
    """Client for interacting with the Nottorney API"""
    
    def __init__(self):
        self.base_url = config.get_api_url()
    
    def _get_headers(self, include_auth=False):
        """Get request headers"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if include_auth:
            # Check if token is expired and refresh if needed
            if config.is_token_expired():
                try:
                    self.refresh_token()
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    # Don't clear tokens here, let the user try again
            
            access_token = config.get_access_token()
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'
        
        return headers
    
    def _make_request(self, method, endpoint, data=None, include_auth=False):
        """Make an HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(include_auth)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            raise NottorneyAPIError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise NottorneyAPIError("Connection error. Please check your internet connection.")
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
                elif 'error' in error_data:
                    error_msg = error_data['error']
            except:
                pass
            raise NottorneyAPIError(error_msg)
        except Exception as e:
            raise NottorneyAPIError(f"Unexpected error: {str(e)}")
    
    # Authentication endpoints
    def login(self, email: str, password: str) -> Dict:
        """
        Login to the Nottorney API
        Returns: { "success": true, "user": {...}, "access_token": "...", "refresh_token": "...", "expires_at": ... }
        """
        data = {
            'email': email,
            'password': password
        }
        
        result = self._make_request('POST', '/addon-login', data)
        
        if result.get('success'):
            # Save tokens to config
            config.save_tokens(
                result['access_token'],
                result['refresh_token'],
                result['expires_at']
            )
            config.save_user(result['user'])
            print(f"Login successful, token expires at: {result['expires_at']}")
        
        return result
    
    def refresh_token(self) -> Dict:
        """
        Refresh the access token using the refresh token
        Returns: { "success": true, "access_token": "...", "refresh_token": "...", "expires_at": ... }
        """
        refresh_token = config.get_refresh_token()
        if not refresh_token:
            raise NottorneyAPIError("No refresh token available")
        
        data = {
            'refresh_token': refresh_token
        }
        
        print(f"Attempting to refresh token...")
        result = self._make_request('POST', '/addon-refresh-token', data)
        
        if result.get('success'):
            # Save new tokens
            config.save_tokens(
                result['access_token'],
                result['refresh_token'],
                result['expires_at']
            )
            print(f"Token refreshed successfully, expires at: {result['expires_at']}")
        
        return result
    
    # Deck endpoints
    def get_purchased_decks(self) -> List[Dict]:
        """
        Get list of decks purchased by the user
        Returns: { "success": true, "decks": [...], "total_count": 5 }
        """
        result = self._make_request('POST', '/addon-get-purchases', include_auth=True)
        
        if result.get('success'):
            return result.get('decks', [])
        
        raise NottorneyAPIError("Failed to get purchased decks")
    
    def download_deck(self, deck_id: str, version: Optional[str] = None) -> Dict:
        """
        Get download URL for a deck
        Returns: { "success": true, "download_url": "...", "deck_title": "...", "version": "...", "expires_in": 3600 }
        """
        data = {
            'deck_id': deck_id
        }
        
        if version:
            data['version'] = version
        
        result = self._make_request('POST', '/addon-download-deck', data, include_auth=True)
        
        if result.get('success'):
            return result
        
        raise NottorneyAPIError("Failed to get download URL")
    
    def download_deck_file(self, download_url: str) -> bytes:
        """
        Download the actual deck file from the download URL
        Returns: The deck file content as bytes
        """
        try:
            response = requests.get(download_url, timeout=120)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise NottorneyAPIError(f"Failed to download deck file: {str(e)}")
    
    # Progress sync endpoint
    def sync_progress(self, progress_data: List[Dict]) -> Dict:
        """
        Sync study progress to the server
        progress_data: [{ "deck_id": "...", "total_cards_studied": 100, ... }]
        Returns: { "success": true, "synced_count": 3 }
        """
        data = {
            'progress': progress_data
        }
        
        result = self._make_request('POST', '/addon-sync-progress', data, include_auth=True)
        
        if result.get('success'):
            return result
        
        raise NottorneyAPIError("Failed to sync progress")


# Global API client instance
api = NottorneyAPI()