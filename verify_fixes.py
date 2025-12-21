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

if __name__ == "__main__":
    test_sql_escaping()
    # test_url_validation removed (legacy .apkg support dropped)
    print("\nVerification complete.")
