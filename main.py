import os
# This ensures the soundfont file path is correct
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from dotenv import load_dotenv
load_dotenv()

from fluidsynth import Synth

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Static, Label, Switch
from textual.events import Click, Key # Simplified imports

# NOTE_TO_MIDI dictionary is unchanged
NOTE_TO_MIDI = {
    "C3": 48, "C#3": 49, "D3": 50, "D#3": 51, "E3": 52,
    "F3": 53, "F#3": 54, "G3": 55, "G#3": 56, "A3": 57,
    "A#3": 58, "B3": 59, "C4": 60, "C#4": 61, "D4": 62,
    "D#4": 63, "E4": 64, "F4": 65, "F#4": 66, "G4": 67,
    "G#4": 68, "A4": 69, "A#4": 70, "B4": 71, "C5": 72, "C#5": 73,
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

    def on_click(self, event: Click) -> None:
        # Simplified call, no longer needs to specify it's a mouse click
        self.app.handle_note_press(self.note)
        event.stop()

class PianoApp(App):
    """A terminal piano application."""
    CSS_PATH = "main.css"
    KEY_MAP = {
        'a': "C3", 'w': "C#3", 's': "D3", 'e': "D#3", 'd': "E3",
        'f': "F3", 't': "F#3", 'g': "G3", 'y': "G#3", 'h': "A3",
        'u': "A#3", 'j': "B3",
    }
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "toggle_sustain", "Sustain"),
        ("ctrl+k", "toggle_keyboard", "Keyboard On/Off")
    ]

    def __init__(self):
        super().__init__()
        self.sustain_on = False
        self.keyboard_active = True
        
        self.fs = Synth()
        # On Windows, use 'dsound'. On Linux, 'alsa' or 'pulseaudio'. 'coreaudio' for macOS.
        self.fs.start(driver='coreaudio') 
        sfid = self.fs.sfload("assets/sounds/GeneralUser.sf2")
        self.fs.program_select(0, sfid, 0, 0)
        
    def on_unmount(self) -> None:
        self.fs.delete()

    # --- NEW: TEXTUAL'S NATIVE KEY HANDLER ---
    # --- NEW: TEXTUAL'S NATIVE KEY HANDLER ---
    def on_key(self, event: Key) -> None:
        """Handles key presses at the application level."""
        
        # First, explicitly check for the tab key to handle the binding
        if event.key == "tab":
            self.action_toggle_sustain()
            event.stop() # Prevent the default tab-to-focus behavior
            return       # Stop processing here

        # If it wasn't tab, proceed with piano key logic
        if not self.keyboard_active:
            return

        if event.key in self.KEY_MAP:
            note = self.KEY_MAP[event.key]
            self.handle_note_press(note)
            event.stop() # Good practice to stop the event after handling

    # --- SIMPLIFIED AND UNIFIED NOTE HANDLING ---
    def handle_note_press(self, note: str):
        """Turns a note's audio and visuals ON."""
        note_id = note.replace("#", "-sharp-")
        try:
            key_widget = self.query_one(f"#{note_id}", PianoKey)
            midi_note = NOTE_TO_MIDI.get(note)

            if midi_note is None:
                return

            self.fs.noteon(0, midi_note, 100)
            key_widget.styles.background = "gold"

            if self.sustain_on:
                # With sustain, flash the key but let the audio continue.
                self.set_timer(0.2, lambda: self.reset_key_visual(key_widget))
            else:
                # No sustain: play for a fixed duration and then release.
                # This works for both mouse clicks and keyboard presses.
                self.set_timer(0.5, lambda: self.handle_note_release(note))
        except:
            pass

    def handle_note_release(self, note: str):
        """Turns a note's audio and visuals OFF."""
        note_id = note.replace("#", "-sharp-")
        try:
            key_widget = self.query_one(f"#{note_id}", PianoKey)
            midi_note = NOTE_TO_MIDI.get(note)
            if midi_note is not None:
                self.fs.noteoff(0, midi_note)
                self.reset_key_visual(key_widget)
        except:
            pass

    def reset_key_visual(self, key_widget: PianoKey):
        """Helper to only reset a key's color."""
        key_widget.styles.background = "black" if key_widget.is_black else "white"

    # --- ACTIONS AND WIDGET EVENTS (NO LONGER NEED THREADING) ---
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Called when the sustain switch is toggled by mouse."""
        if event.switch.id == "sustain-switch":
            self.sustain_on = event.value
            self.update_sustain_state()

    def action_toggle_sustain(self) -> None:
        """Action for the Tab key binding."""
        self.query_one("#sustain-switch", Switch).toggle()

    def update_sustain_state(self):
        """Central method to update the synthesizer and visuals."""
        sustain_value = 127 if self.sustain_on else 0
        self.fs.cc(0, 64, sustain_value)
        if not self.sustain_on:
            self.fs.all_notes_off(0)
            for key_widget in self.query(PianoKey):
                self.reset_key_visual(key_widget)

    def action_toggle_keyboard(self) -> None:
        """Toggles keyboard input."""
        self.keyboard_active = not self.keyboard_active
        header = self.query_one(Header)
        header.sub_title = "A Piano in Your Terminal" if self.keyboard_active else "Keyboard OFF (Press Ctrl+K)"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="controls-container"):
            yield Label("Sustain:")
            yield Switch(id="sustain-switch")
        with Container(id="piano-container"):
            for note in NOTE_TO_MIDI:
                key_char = next((k for k, v in self.KEY_MAP.items() if v == note), "")
                is_black = "#" in note
                note_id = note.replace("#", "-sharp-")
                yield PianoKey(note, key_char, is_black, id=note_id)
        yield Footer()
        
if __name__ == "__main__":
    app = PianoApp()
    app.run()