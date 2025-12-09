"""
Progress syncing for the Nottorney addon
Syncs study progress to the server
"""

from aqt import mw
from datetime import datetime, timedelta
from .api_client import api
from .config import config
from .deck_importer import get_deck_stats


def get_progress_data() -> list:
    """
    Get progress data for all downloaded Nottorney decks
    
    Returns:
        List of progress data dictionaries
    """
    downloaded_decks = config.get_downloaded_decks()
    progress_data = []
    
    for deck_id, deck_info in downloaded_decks.items():
        anki_deck_id = deck_info.get('anki_deck_id')
        
        if not anki_deck_id:
            continue
        
        # Get deck statistics
        stats = get_deck_stats(anki_deck_id)
        
        if not stats:
            continue
        
        # Get review statistics from the last 30 days
        review_stats = get_review_stats_for_deck(anki_deck_id, days=30)
        
        # Build progress data
        progress = {
            'deck_id': deck_id,
            'total_cards': stats.get('total_cards', 0),
            'total_cards_studied': review_stats.get('total_reviews', 0),
            'new_cards_studied': review_stats.get('new_cards', 0),
            'cards_mastered': stats.get('review_cards', 0),
            'average_ease': review_stats.get('average_ease', 0),
            'study_time_minutes': review_stats.get('study_time_minutes', 0),
            'last_study_date': review_stats.get('last_study_date'),
            'synced_at': datetime.now().isoformat()
        }
        
        progress_data.append(progress)
    
    return progress_data


def get_review_stats_for_deck(deck_id: int, days: int = 30) -> dict:
    """
    Get review statistics for a deck from the review history
    
    Args:
        deck_id: The Anki deck ID
        days: Number of days to look back
    
    Returns:
        Dictionary with review statistics
    """
    try:
        # Calculate the timestamp for X days ago
        cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        # Get card IDs for the deck
        card_ids = mw.col.decks.cids(deck_id, children=True)
        
        if not card_ids:
            return {}
        
        # Query the review log
        card_ids_str = ",".join(str(cid) for cid in card_ids)
        
        query = f"""
            SELECT 
                COUNT(*) as total_reviews,
                SUM(CASE WHEN type = 0 THEN 1 ELSE 0 END) as new_cards,
                AVG(ease) as average_ease,
                SUM(time) / 60000 as study_time_minutes,
                MAX(id) as last_review_id
            FROM revlog
            WHERE cid IN ({card_ids_str})
            AND id >= {cutoff_time}
        """
        
        result = mw.col.db.first(query)
        
        if not result:
            return {}
        
        # Get last study date from the last review ID
        last_study_date = None
        if result[4]:  # last_review_id
            last_study_date = datetime.fromtimestamp(result[4] / 1000).isoformat()
        
        return {
            'total_reviews': result[0] or 0,
            'new_cards': result[1] or 0,
            'average_ease': round(result[2] or 0, 2),
            'study_time_minutes': round(result[3] or 0, 2),
            'last_study_date': last_study_date
        }
    except Exception as e:
        print(f"Error getting review stats: {e}")
        return {}


def sync_progress():
    """
    Sync progress for all downloaded decks to the server
    """
    if not config.is_logged_in():
        raise Exception("Not logged in")
    
    # Get progress data
    progress_data = get_progress_data()
    
    if not progress_data:
        # No decks to sync
        print("No decks to sync")
        return None
    
    # Send to server
    print(f"Syncing progress for {len(progress_data)} deck(s)")
    result = api.sync_progress(progress_data)
    
    return result


def should_auto_sync() -> bool:
    """
    Check if we should automatically sync progress
    (e.g., hasn't been synced in the last hour)
    """
    # You can implement logic here to check when the last sync was
    # For now, we'll just return True
    return True


def auto_sync_if_needed():
    """
    Automatically sync progress if needed
    """
    if not config.is_logged_in():
        return
    
    if not should_auto_sync():
        return
    
    try:
        sync_progress()
    except Exception as e:
        # Silently fail for auto-sync
        # You can log this if you implement logging
        print(f"Auto-sync failed: {e}")