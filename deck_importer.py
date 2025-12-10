"""
Deck importer for the Nottorney addon - FIXED VERSION
Handles importing .apkg files into Anki without creating duplicate decks
"""

import tempfile
import os
from pathlib import Path
from aqt import mw
from aqt.operations import QueryOp
from anki.collection import ImportAnkiPackageRequest


def import_deck(deck_content: bytes, deck_name: str) -> int:
    """
    Import a deck into Anki from .apkg file content
    
    Args:
        deck_content: The .apkg file content as bytes
        deck_name: Name of the deck (used for reference only)
    
    Returns:
        The Anki deck ID of the imported deck
    """
    # Create a temporary file to store the .apkg
    with tempfile.NamedTemporaryFile(suffix='.apkg', delete=False) as temp_file:
        temp_file.write(deck_content)
        temp_file_path = temp_file.name
    
    try:
        # Store existing deck IDs to find the new one
        existing_deck_ids = set(mw.col.decks.all_names_and_ids())
        
        # Use the modern import method for Anki 2.1.55+
        request = ImportAnkiPackageRequest(
            package_path=temp_file_path
        )
        
        # Import the deck
        result = mw.col.import_anki_package(request)
        
        # Find the newly imported deck(s)
        new_deck_ids = set(mw.col.decks.all_names_and_ids()) - existing_deck_ids
        
        if new_deck_ids:
            # Get the first new deck (usually there's only one)
            new_deck = list(new_deck_ids)[0]
            deck_id = new_deck.id
            actual_deck_name = new_deck.name
            
            print(f"✓ Imported deck: '{actual_deck_name}' (ID: {deck_id})")
            
            # Optional: Rename the deck to match Nottorney's name if different
            if actual_deck_name != deck_name:
                print(f"  Note: Deck imported as '{actual_deck_name}', not '{deck_name}'")
                # You can uncomment the next line to rename the deck:
                # mw.col.decks.rename(mw.col.decks.get(deck_id), deck_name)
        else:
            # Fallback: Try to find by name if no new decks detected
            # This might happen if the deck already exists
            print(f"⚠ No new deck detected, searching for existing deck by name...")
            
            # Search for deck by the name that might be in the package
            all_decks = mw.col.decks.all_names_and_ids()
            
            # Try to find a deck that matches or contains the deck_name
            matching_deck = None
            for deck_info in all_decks:
                if deck_name.lower() in deck_info.name.lower():
                    matching_deck = deck_info
                    break
            
            if matching_deck:
                deck_id = matching_deck.id
                print(f"✓ Found existing deck: '{matching_deck.name}' (ID: {deck_id})")
            else:
                # Last resort: get the most recently modified deck
                all_deck_dicts = [mw.col.decks.get(d.id) for d in all_decks]
                most_recent = max(all_deck_dicts, key=lambda d: d.get('mod', 0))
                deck_id = most_recent['id']
                print(f"⚠ Using most recent deck: '{most_recent['name']}' (ID: {deck_id})")
        
        # Refresh the main window to show the new deck
        mw.reset()
        
        return deck_id
    
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass


def import_deck_with_progress(deck_content: bytes, deck_name: str, 
                              on_success=None, on_failure=None):
    """
    Import a deck with progress tracking (runs in background)
    
    Args:
        deck_content: The .apkg file content as bytes
        deck_name: Name of the deck
        on_success: Callback function when import succeeds (receives deck_id)
        on_failure: Callback function when import fails (receives error message)
    """
    def import_in_background():
        return import_deck(deck_content, deck_name)
    
    def on_done(deck_id):
        if on_success:
            on_success(deck_id)
    
    def on_error(error):
        error_msg = str(error)
        if on_failure:
            on_failure(error_msg)
    
    # Use Anki's QueryOp for background operations
    op = QueryOp(
        parent=mw,
        op=lambda col: import_in_background(),
        success=on_done
    )
    op.failure(on_error)
    op.run_in_background()


def get_deck_stats(deck_id: int) -> dict:
    """
    Get statistics for a deck
    
    Args:
        deck_id: The Anki deck ID
    
    Returns:
        Dictionary with deck statistics
    """
    deck = mw.col.decks.get(deck_id)
    
    if not deck:
        return {}
    
    # Get card counts
    card_ids = mw.col.decks.cids(deck_id, children=True)
    total_cards = len(card_ids)
    
    # Count new, learning, and review cards
    new_cards = 0
    learning_cards = 0
    review_cards = 0
    
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        if card.type == 0:  # New
            new_cards += 1
        elif card.type == 1:  # Learning
            learning_cards += 1
        elif card.type == 2:  # Review
            review_cards += 1
    
    return {
        'name': deck['name'],
        'total_cards': total_cards,
        'new_cards': new_cards,
        'learning_cards': learning_cards,
        'review_cards': review_cards
    }


def get_all_deck_stats() -> list:
    """
    Get statistics for all decks
    
    Returns:
        List of deck statistics
    """
    all_decks = mw.col.decks.all()
    stats = []
    
    for deck in all_decks:
        deck_id = deck['id']
        deck_stats = get_deck_stats(deck_id)
        if deck_stats:
            stats.append(deck_stats)
    
    return stats