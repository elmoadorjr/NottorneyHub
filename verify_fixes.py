"""
Verification script for AnkiPH Addon fixes
"""

import sys
import os
from unittest.mock import MagicMock

# Add addon directory to path
addon_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(addon_dir)

def test_sql_escaping():
    print("Testing SQL escaping...")
    from utils import escape_anki_search
    
    test_cases = [
        ('Normal Deck', 'Normal Deck'),
        ('Deck (with) Parentheses', 'Deck \\(with\\) Parentheses'),
        ('Deck "with" Quotes', 'Deck "with" Quotes'),  # Anki handles quotes differently
        ('Deck with * Asterisk', 'Deck with \\* Asterisk'),
    ]
    
    for input_str, expected in test_cases:
        result = escape_anki_search(input_str)
        if result == expected:
            print(f"✓ '{input_str}' -> '{result}'")
        else:
            print(f"✗ '{input_str}' -> '{result}' (expected '{expected}')")

def test_url_validation():
    print("\nTesting URL validation...")
    from api_client import ApiClient, AnkiPHAPIError
    client = ApiClient()
    
    valid_urls = [
        "https://example.com/deck.apkg",
        "http://test.org/file?v=1",
    ]
    
    invalid_urls = [
        "not-a-url",
        "ftp://imsecure.com",
        "javascript:alert(1)",
        "",
        None
    ]
    
    for url in valid_urls:
        try:
            # We don't actually want to download, just test the validation before requests.get
            # Mocking requests.get to prevent actual network call
            import requests
            requests.get = MagicMock()
            client.download_deck_file(url)
            print(f"✓ Valid URL accepted: {url}")
        except Exception as e:
            print(f"✗ Valid URL rejected: {url} ({e})")
            
    for url in invalid_urls:
        try:
            client.download_deck_file(url)
            print(f"✗ Invalid URL accepted: {url}")
        except AnkiPHAPIError as e:
            print(f"✓ Invalid URL rejected: {url} ({e})")
        except Exception as e:
            print(f"✗ Unexpected error for {url}: {e}")

if __name__ == "__main__":
    test_sql_escaping()
    test_url_validation()
    print("\nVerification complete.")
