"""
Deck importer for the AnkiPH addon
Handles importing deck data directly from JSON into Anki (Database-Only Sync)
Version: 3.0.0
"""

import os
import requests
from typing import Dict, List, Optional, Any
from aqt import mw
from aqt.operations import QueryOp
from aqt.utils import showInfo
from anki.notes import Note
from .logger import logger

def import_deck_from_json(deck_data: Dict, deck_name: str) -> int:
    """
    Import a deck into Anki from a JSON dictionary (v3.0+ format)
    
    Args:
        deck_data: The deck data dictionary containing 'deck', 'cards', 'note_types', 'media_files'
        deck_name: Name of the deck
    
    Returns:
        The Anki deck ID of the imported/updated deck
    """
    if not deck_data:
        raise Exception("Deck data is empty")
        
    try:
        logger.info(f"Starting import for deck: {deck_name}")
        
        # 1. Sync Note Types
        note_types = deck_data.get('note_types', [])
        _sync_note_types(note_types)
        
        # 2. Get/Create Deck
        # Use the name from the JSON if available, otherwise fallback to arg
        api_deck = deck_data.get('deck', {})
        target_deck_name = api_deck.get('title') or deck_name
        
        # Ensure deck exists
        deck_id = mw.col.decks.id(target_deck_name)
        # Select it (optional, but good for UI)
        mw.col.decks.select(deck_id)
        
        # Update deck configuration if needed (optional)
        # This is where we could set deck options if provided in JSON
        
        # 3. Sync Media
        media_files = deck_data.get('media_files', []) # List of {filename, url} or Dict
        _sync_media_files(media_files)
        
        # 4. Sync Cards/Notes
        cards = deck_data.get('cards', [])
        logger.info(f"Syncing {len(cards)} cards...")
        
        new_cnt = 0
        upd_cnt = 0
        
        for card_data in cards:
            if _process_card(card_data, deck_id):
                new_cnt += 1
            else:
                upd_cnt += 1
                
        logger.info(f"Import complete: {new_cnt} new notes, {upd_cnt} updated notes")
        
        # Reset UI
        mw.reset()
        
        return int(deck_id)
        
    except Exception as e:
        logger.exception(f"Import failed: {e}")
        raise

def _sync_note_types(note_types: List[Dict]):
    """Ensure note types exist and match the definition"""
    for nt_data in note_types:
        name = nt_data.get('name')
        if not name:
            continue
            
        model = mw.col.models.by_name(name)
        
        # If model doesn't exist, create it
        if not model:
            logger.info(f"Creating new note type: {name}")
            model = mw.col.models.new(name)
            
            # Fields
            for field in nt_data.get('fields', []):
                # Fields in v3 might be objects or strings
                field_name = field.get('name') if isinstance(field, dict) else field
                mw.col.models.add_field(model, mw.col.models.new_field(field_name))
                
            # Templates
            for tmpl in nt_data.get('templates', []):
                t = mw.col.models.new_template(tmpl.get('name', 'Card 1'))
                t['qfmt'] = tmpl.get('qfmt', '')
                t['afmt'] = tmpl.get('afmt', '')
                mw.col.models.add_template(model, t)
                
            # CSS
            if 'css' in nt_data:
                model['css'] = nt_data['css']
                
            mw.col.models.add(model)
            mw.col.models.save(model)
        
        # Note: Full model updating logic (handling schema changes) is complex.
        # For now, we assume if it exists, it's compatible, or we might miss field updates.
        # Future improvement: Compare fields and add missing ones.

def _sync_media_files(media_files: Any):
    """Download missing media files"""
    # Handle list of dicts or dict of filename:url
    if isinstance(media_files, dict):
        items = media_files.items()
    else:
        # Assuming list of dicts like [{'filename': 'x.jpg', 'url': '...'}]
        items = []
        for m in media_files:
            if 'filename' in m and 'url' in m:
                items.append((m['filename'], m['url']))
                
    for filename, url in items:
        # Check if exists
        if os.path.exists(os.path.join(mw.col.media.dir(), filename)):
            continue
            
        try:
            # Download
            logger.debug(f"Downloading media: {filename}")
            if hasattr(url, 'startswith') and url.startswith('http'):
                 r = requests.get(url, timeout=30)
                 if r.status_code == 200:
                     mw.col.media.write_data(filename, r.content)
        except Exception as e:
            logger.warning(f"Failed to download media {filename}: {e}")

def _process_card(card_data: Dict, deck_id: int) -> bool:
    """
    Create or update a note from card data.
    Returns True if new note created, False if updated.
    
    Assumes card_data has:
    - guid (str)
    - note_type (str)
    - fields (Dict[str, str] or List[str])
    - tags (List[str], optional)
    """
    guid = card_data.get('guid')
    if not guid:
        return False
    
    existing_note = mw.col.get_note(mw.col.find_notes(f"guid:{guid}")[0]) if mw.col.find_notes(f"guid:{guid}") else None
    
    if existing_note:
        # Update existing
        return _update_note(existing_note, card_data, deck_id)
    else:
        # Create new
        return _create_note(card_data, deck_id)

def _create_note(card_data: Dict, deck_id: int) -> bool:
    model_name = card_data.get('note_type')
    model = mw.col.models.by_name(model_name)
    if not model:
        logger.error(f"Model {model_name} not found for card {card_data.get('guid')}")
        return False
        
    note = mw.col.new_note(model)
    note.guid = card_data.get('guid')
    
    _fill_note_fields(note, card_data.get('fields', {}))
    
    # Tags
    tags = card_data.get('tags', [])
    if tags:
        note.tags = tags
        
    # Add note
    mw.col.add_note(note, deck_id)
    return True

def _update_note(note: Note, card_data: Dict, deck_id: int) -> bool:
    # Update fields
    changes = False
    
    if _fill_note_fields(note, card_data.get('fields', {})):
        changes = True
        
    # Update tags
    new_tags = card_data.get('tags', [])
    if set(note.tags) != set(new_tags):
        note.tags = new_tags
        changes = True
        
    # Force move to correct deck if needed? 
    # Usually cards are in decks, notes are just notes. 
    # But for a single-deck download, we expect cards to be in that deck.
    # Changing deck for all cards of this note:
    for card in note.cards():
        if card.did != deck_id:
            card.did = deck_id
            card.flush()
            
    if changes:
        note.flush()
        
    return False

def _fill_note_fields(note: Note, fields_data: Any) -> bool:
    """Populate note fields. Returns True if any field changed."""
    changed = False
    model_fields = mw.col.models.field_names(note.note_type())
    # O(1) lookup
    model_field_set = set(model_fields)
    
    # Handle dict (field_name: value)
    if isinstance(fields_data, dict):
        for fname, fval in fields_data.items():
            if fname in model_field_set:
                if note[fname] != fval:
                    note[fname] = fval
                    changed = True
            else:
                # Log warning for debugging data mismatches
                logger.debug(f"Field '{fname}' not found in note type '{note.note_type()['name']}'")
                    
    # Handle list (values in order)
    elif isinstance(fields_data, list):
        for i, fval in enumerate(fields_data):
            if i < len(model_fields):
                fname = model_fields[i]
                if note[fname] != fval:
                    note[fname] = fval
                    changed = True
                    
    return changed


def import_deck_with_progress(deck_data_provider, deck_name: str, 
                              on_success=None, on_failure=None, parent=None):
    """
    Import a deck with progress tracking (runs in background)
    
    Args:
        deck_data_provider: Function that returns the deck data dict (api call)
                            OR the dict itself
        deck_name: Name of the deck
        on_success: Callback(deck_id)
        on_failure: Callback(error_msg)
        parent: Parent widget
    """
    if parent is None:
        parent = mw
    
    def background_op():
        # Clean way to fetch data inside the thread if a provider func is passed
        data = deck_data_provider() if callable(deck_data_provider) else deck_data_provider
        return import_deck_from_json(data, deck_name)
    
    def on_done(deck_id):
        logger.info(f"Background import succeeded: {deck_id}")
        if on_success:
            on_success(int(deck_id))
            
    def on_error(error):
        msg = str(error)
        logger.error(f"Background import failed: {msg}")
        if on_failure:
            on_failure(msg)
            
    op = QueryOp(
        parent=parent,
        op=lambda col: background_op(),
        success=on_done
    )
    op.failure(on_error)
    op.run_in_background()


# Keep existing utility functions for compatibility/utility
def get_deck_stats(deck_id: int) -> dict:
    # ... (same as before) ...
    try:
        deck_id = int(deck_id)
        deck = mw.col.decks.get(deck_id)
        if not deck: return {}
        
        card_ids = mw.col.decks.cids(deck_id, children=True)
        total = len(card_ids)
        new_c = learning_c = review_c = 0
        
        for cid in card_ids:
            try:
                c = mw.col.get_card(cid)
                if c.type == 0: new_c += 1
                elif c.type == 1: learning_c += 1
                elif c.type == 2: review_c += 1
            except: pass
            
        return {
            'name': deck['name'],
            'total_cards': total,
            'new_cards': new_c,
            'learning_cards': learning_c,
            'review_cards': review_c
        }
    except:
        return {}

def deck_exists(deck_id: int) -> bool:
    try:
        return mw.col.decks.get(int(deck_id)) is not None
    except:
        return False

def delete_deck(deck_id: int) -> bool:
    try:
        mw.col.decks.remove([int(deck_id)])
        mw.reset()
        return True
    except:
        return False