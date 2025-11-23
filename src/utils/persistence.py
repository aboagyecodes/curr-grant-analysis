"""
Persistence Utilities

Handles saving and loading user research notes for anomalies.
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import CACHE_DIR


NOTES_FILE = os.path.join(CACHE_DIR, 'anomaly_notes.json')


def load_notes():
    """
    Load user research notes from JSON
    
    Returns:
        dict: {anomaly_id: note_text}
    """
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_note(anomaly_id, note_text):
    """
    Save a research note for an anomaly
    
    Args:
        anomaly_id: Unique identifier for anomaly (e.g., "2023-01-15_2023-02-10")
        note_text: User's research note
    """
    notes = load_notes()
    notes[anomaly_id] = note_text
    
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2)


def get_note(anomaly_id):
    """
    Get a note for a specific anomaly
    
    Args:
        anomaly_id: Anomaly identifier
    
    Returns:
        str: Note text or empty string
    """
    notes = load_notes()
    return notes.get(anomaly_id, '')


def generate_anomaly_id(anomaly):
    """
    Generate unique ID for an anomaly
    
    Args:
        anomaly: Anomaly dict with start_date, end_date
    
    Returns:
        str: Unique ID
    """
    import pandas as pd
    start = pd.to_datetime(anomaly['start_date']).strftime('%Y-%m-%d')
    end = pd.to_datetime(anomaly['end_date']).strftime('%Y-%m-%d')
    return f"{start}_{end}"


if __name__ == '__main__':
    print("Persistence utilities loaded")
