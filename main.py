from dotenv import load_dotenv
load_dotenv()
from fluidsynth import Synth

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static
from textual.events import Click
from textual.events import Key

# Defines the full two-octave range we will display
# Add the last two keys to complete the octave
NOTE_TO_MIDI = {
    "C3": 48, "C#3": 49, "D3": 50, "D#3": 51, "E3": 52,
    "F3": 53, "F#3": 54, "G3": 55, "G#3": 56, "A3": 57,
    "A#3": 58, "B3": 59,
    "C4": 60, "C#4": 61, "D4": 62, "D#4": 63, "E4": 64,
    "F4": 65, "F#4": 66, "G4": 67, "G#4": 68, "A4": 69,
    "A#4": 70, "B4": 71,
    # --- NEW KEYS ---
    "C5": 72, "C#5": 73,
}

class PianoKey(Static):
    """A single piano key widget."""
    def __init__(self, note: str, keyboard_key: str, is_black: bool, **kwargs) -> None:
        super().__init__(keyboard_key, **kwargs)
        self.note = note
        self.keyboard_key = keyboard_key
        self.is_black = is_black
        self.add_class("key")
        self.add_class("black_key" if is_black else "white_key")
        self.animating = False

    def on_click(self, event: Click) -> None:
        self.app.play_note(self.note)
        event.stop()

class PianoApp(App):
    """A terminal piano application."""
    CSS_PATH = "main.css"

    # Keyboard mappings for the first octave (for chords)
    KEY_MAP = {
        "C3": "a", "C#3": "w", "D3": "s", "D#3": "e", "E3": "d",
        "F3": "f", "F#3": "t", "G3": "g", "G#3": "y", "A3": "h",
        "A#3": "u", "B3": "j", "C4": "k"
    }
    
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.fs = Synth()
        self.fs.start(driver='coreaudio')
        sfid = self.fs.sfload("assets/sounds/GeneralUser.sf2")
        self.fs.program_select(0, sfid, 0, 0)

    def on_unmount(self) -> None:
        self.fs.delete()

    def play_note(self, note: str) -> None:
        note_id = note.replace("#", "-sharp-")
        key_widget = self.query_one(f"#{note_id}", PianoKey)
        
        if key_widget.animating:
            return

        midi_note = NOTE_TO_MIDI.get(note)
        if midi_note is None:
            return

        key_widget.animating = True
        self.fs.noteon(0, midi_note, 100)
        note_duration = 0.7
        self.set_timer(note_duration, lambda: self.fs.noteoff(0, midi_note))
        original_color = key_widget.styles.background
        def restore_color_and_state():
            key_widget.styles.background = original_color
            key_widget.animating = False
        key_widget.styles.background = "gold"
        self.set_timer(note_duration, restore_color_and_state)
        
    def on_key(self, event: Key) -> None:
        note_to_play = next(
            (note for note, key in self.KEY_MAP.items() if key == event.key), None
        )
        if note_to_play:
            self.play_note(note_to_play)

    # UPDATED: compose method now draws the final two-octave layout
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="piano-container"):
            # We iterate through all notes defined in NOTE_TO_MIDI
            for note in NOTE_TO_MIDI:
                # Check if this note has a keyboard mapping, otherwise it's mouse-only
                key_char = self.KEY_MAP.get(note, "")
                is_black = "#" in note
                note_id = note.replace("#", "-sharp-")
                yield PianoKey(note, key_char, is_black, id=note_id)
        yield Footer()

if __name__ == "__main__":
    app = PianoApp()
    app.run()