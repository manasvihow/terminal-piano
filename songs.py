# songs.py

# Data structure: { "Song Title": [(start_time, ["NOTE1", "NOTE2"], duration), ...], ... }

SONGS = {
    "Für Elise (Easy Mouse Version)": [
        # --- Simplified Arrangement ---
        # Right hand melody is slower, one note at a time.
        # Left hand plays simple, long two-note chords.
        
        # Measure 1
        (0.0, ["E5"], 0.4), (0.5, ["D#5"], 0.4),
        (1.0, ["E5"], 0.4), (1.5, ["D#5"], 0.4),
        (2.0, ["E5"], 0.4), (2.5, ["B4"], 0.4),
        (3.0, ["D5"], 0.4), (3.5, ["C5"], 0.4),
        # Simple Left Hand Chord
        (0.0, ["A2", "A3"], 3.9),

        # Measure 2
        (4.0, ["A4"], 1.9),
        # Simple Left Hand Chord
        (4.0, ["C3", "C4"], 1.9),

        # Measure 3
        (6.0, ["E4"], 0.4), (6.5, ["A4"], 0.4), (7.0, ["B4"], 1.9),
        # Simple Left Hand Chord
        (6.0, ["E2", "E3"], 3.9),

        # Measure 4
        (8.0, ["E4"], 1.9),
         # Simple Left Hand Chord
        (8.0, ["A2", "A3"], 1.9),
    ],
    "Twinkle Twinkle Little Star": [
        (0.0, ["C4"], 0.4), (0.5, ["C4"], 0.4), (1.0, ["G4"], 0.4), (1.5, ["G4"], 0.4),
        (2.0, ["A4"], 0.4), (2.5, ["A4"], 0.4), (3.0, ["G4"], 0.9),
    ],
}

# In songs.py

# --- UPDATED: Range is now C3 to C7 ---
NOTE_TO_MIDI = {
    "C3": 48, "C#3": 49, "D3": 50, "D#3": 51, "E3": 52, "F3": 53, "F#3": 54,
    "G3": 55, "G#3": 56, "A3": 57, "A#3": 58, "B3": 59,
    "C4": 60, "C#4": 61, "D4": 62, "D#4": 63, "E4": 64, "F4": 65, "F#4": 66,
    "G4": 67, "G#4": 68, "A4": 69, "A#4": 70, "B4": 71,
    "C5": 72, "C#5": 73, "D5": 74, "D#5": 75, "E5": 76, "F5": 77, "F#5": 78,
    "G5": 79, "G#5": 80, "A5": 81, "A#5": 82, "B5": 83,
    "C6": 84, "C#6": 85, "D6": 86, "D#6": 87, "E6": 88, "F6": 89, "F#6": 90,
    "G6": 91, "G#6": 92, "A6": 93, "A#6": 94, "B6": 95,
    "C7": 96,
}