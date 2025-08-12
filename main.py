from dotenv import load_dotenv
load_dotenv()
from fluidsynth import Synth

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static
from textual.events import Click
from textual.events import Key

# A mapping from our note names to MIDI note numbers
NOTE_TO_MIDI = {
    "C4": 60, "C#4": 61, "D4": 62, "D#4": 63, "E4": 64,
    "F4": 65, "F#4": 66, "G4": 67, "G#4": 68, "A4": 69,
    "A#4": 70, "B4": 71, "C5": 72, "C#5": 73, "D5": 74,
    "D#5": 75, "E5": 76,
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
        # Add the flag to track animation state
        self.animating = False

    def on_click(self, event: Click) -> None:
        """Called when the user clicks the widget."""
        self.app.play_note(self.note)
        event.stop()

class PianoApp(App):
    """A terminal piano application."""
    CSS_PATH = "main.css"

    KEY_MAP = {
        "C4": "a", "C#4": "w", "D4": "s", "D#4": "e", "E4": "d",
        "F4": "f", "F#4": "t", "G4": "g", "G#4": "y", "A4": "h",
        "A#4": "u", "B4": "j", "C5": "k", "C#5": "o", "D5": "l",
        "D#5": "p", "E5": ";",
    }
    
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        # --- FluidSynth Setup ---
        self.fs = Synth()
        self.fs.start() # You may need to specify a driver, e.g., self.fs.start(driver='coreaudio')
        
        # Load the SoundFont file.
        # MAKE SURE TO REPLACE 'GeneralUser.sf2' WITH YOUR FILENAME
        sfid = self.fs.sfload("assets/sounds/GeneralUser.sf2")
        # Select the piano sound (program 0) on channel 0
        self.fs.program_select(0, sfid, 0, 0)

    def on_unmount(self) -> None:
        """Cleanly shut down the synthesizer when the app quits."""
        self.fs.delete()

    def play_note(self, note: str) -> None:
        """Play a note using FluidSynth."""
        note_id = note.replace("#", "-sharp-")
        key_widget = self.query_one(f"#{note_id}", PianoKey)
        
        # If the key is already animating, do nothing. This prevents the bug.
        if key_widget.animating:
            return

        midi_note = NOTE_TO_MIDI.get(note)
        if midi_note is None:
            return

        # --- New Audio & Animation Logic ---
        key_widget.animating = True # Set the flag to block other presses
        self.fs.noteon(0, midi_note, 100)

        note_duration = 0.7
        self.set_timer(note_duration, lambda: self.fs.noteoff(0, midi_note))

        original_color = key_widget.styles.background
        
        # This function will run after the timer is done
        def restore_color_and_state():
            key_widget.styles.background = original_color
            key_widget.animating = False # Reset the flag to allow another press

        key_widget.styles.background = "gold"
        self.set_timer(note_duration, restore_color_and_state)
        
    def on_key(self, event: Key) -> None:
        """Called when the user presses a key."""
        note_to_play = next(
            (note for note, key in self.KEY_MAP.items() if key == event.key), None
        )
        if note_to_play:
            self.play_note(note_to_play)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container(id="piano-container"):
            for note, key in self.KEY_MAP.items():
                is_black = "#" in note
                note_id = note.replace("#", "-sharp-")
                yield PianoKey(note, key, is_black, id=note_id)
        yield Footer()

if __name__ == "__main__":
    app = PianoApp()
    app.run()