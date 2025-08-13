import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from dotenv import load_dotenv
load_dotenv()

from fluidsynth import Synth
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Static, Label, Switch
from textual.events import Key
from textual.reactive import reactive
from textual.dom import NoMatches

# NOTE: The NOTE_TO_MIDI dictionary remains unchanged.
NOTE_TO_MIDI = {
    "C3": 48, "C#3": 49, "D3": 50, "D#3": 51, "E3": 52,
    "F3": 53, "F#3": 54, "G3": 55, "G#3": 56, "A3": 57,
    "A#3": 58, "B3": 59, "C4": 60, "C#4": 61, "D4": 62,
    "D#4": 63, "E4": 64, "F4": 65, "F#4": 66, "G4": 67,
    "G#4": 68, "A4": 69, "A#4": 70, "B4": 71, "C5": 72, "C#5": 73,
}

class PianoKey(Static):
    """A single piano key widget that knows its own state."""
    def __init__(self, note: str, keyboard_key: str, is_black: bool, **kwargs) -> None:
        super().__init__(keyboard_key, **kwargs)
        self.note = note
        self.keyboard_key = keyboard_key
        self.is_black = is_black
        self.add_class("key")
        self.add_class("key--black" if is_black else "key--white")

    def on_click(self) -> None:
        self.app.handle_note_press(self.note)

class PianoApp(App):
    """A terminal piano application using idiomatic Textual features."""
    CSS_PATH = "main.tcss"
    
    # --- UPDATED: More keys have been mapped for the C4 octave ---
    KEY_MAP = {
        'a': "C3", 'w': "C#3", 's': "D3", 'e': "D#3", 'd': "E3",
        'f': "F3", 't': "F#3", 'g': "G3", 'y': "G#3", 'h': "A3",
        'u': "A#3", 'j': "B3",
        'k': "C4", 'o': "C#4", 'l': "D4", 'p': "D#4", ';': "E4",
        "'": "F4", '[': "F#4", ']': "G4", '\\': "G#4",
    }
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "toggle_sustain", "Sustain On/Off"),
        ("ctrl+k", "toggle_keyboard", "Keyboard On/Off")
    ]

    sustain_on = reactive(False)
    keyboard_active = reactive(True)

    def __init__(self):
        super().__init__()
        self.fs = Synth()
        self.fs.start(driver='coreaudio')
        sfid = self.fs.sfload("assets/sounds/GeneralUser.sf2")
        self.fs.program_select(0, sfid, 0, 0)

    def on_unmount(self) -> None:
        self.fs.delete()

    def watch_sustain_on(self, sustain_on: bool) -> None:
        sustain_value = 127 if sustain_on else 0
        self.fs.cc(0, 64, sustain_value)
        if not sustain_on:
            self.fs.all_notes_off(0)
            for key_widget in self.query(".key--pressed"):
                key_widget.remove_class("key--pressed")

    def watch_keyboard_active(self, keyboard_active: bool) -> None:
        new_title = "A Piano in Your Terminal" if keyboard_active else "Keyboard OFF (Press Ctrl+K)"
        self.query_one(Header).sub_title = new_title

    # --- FIX: The Tab key is now explicitly handled here to override default focus behavior ---
    def on_key(self, event: Key) -> None:
        """Handles key presses."""
        # Handle the sustain toggle binding manually to prevent focus switching.
        if event.key == "tab":
            self.action_toggle_sustain()
            event.stop()  # Stop the event from bubbling up
            return

        # Handle piano key presses
        if self.keyboard_active and event.key in self.KEY_MAP:
            note = self.KEY_MAP[event.key]
            self.handle_note_press(note)

    def handle_note_press(self, note: str):
        midi_note = NOTE_TO_MIDI.get(note)
        if midi_note is None:
            return

        note_id = note.replace("#", "-sharp-")
        try:
            key_widget = self.query_one(f"#{note_id}", PianoKey)
            key_widget.add_class("key--pressed")
            self.fs.noteon(0, midi_note, 100)

            if self.sustain_on:
                self.set_timer(0.2, lambda: key_widget.remove_class("key--pressed"))
            else:
                self.set_timer(0.5, lambda: self.handle_note_release(note))
        except NoMatches:
            self.log(f"Warning: No widget found for note {note}")

    def handle_note_release(self, note: str):
        midi_note = NOTE_TO_MIDI.get(note)
        note_id = note.replace("#", "-sharp-")
        try:
            key_widget = self.query_one(f"#{note_id}", PianoKey)
            key_widget.remove_class("key--pressed")
            if midi_note is not None:
                self.fs.noteoff(0, midi_note)
        except NoMatches:
            pass

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "sustain-switch":
            self.sustain_on = event.value

    def action_toggle_sustain(self) -> None:
        self.query_one("#sustain-switch", Switch).toggle()

    def action_toggle_keyboard(self) -> None:
        self.keyboard_active = not self.keyboard_active

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        # --- FINAL FIX: Controls are now docked via CSS ---
        with Horizontal(id="controls-container"):
            yield Label("Sustain:")
            yield Switch(id="sustain-switch")
        
        # The grid will fill the remaining space
        with Container(id="centering-grid"):
            yield Static()  # Left spacer
            with Container(id="piano-container"):
                # First, draw all the WHITE keys
                for note in NOTE_TO_MIDI:
                    if "#" not in note:
                        key_char = next((k for k, v in self.KEY_MAP.items() if v == note), "")
                        note_id = note.replace("#", "-sharp-")
                        yield PianoKey(note, key_char, is_black=False, id=note_id)

                # Second, draw all the BLACK keys on top
                for note in NOTE_TO_MIDI:
                    if "#" in note:
                        key_char = next((k for k, v in self.KEY_MAP.items() if v == note), "")
                        note_id = note.replace("#", "-sharp-")
                        yield PianoKey(note, key_char, is_black=True, id=note_id)
            yield Static()  # Right spacer

        yield Footer()

if __name__ == "__main__":
    app = PianoApp()
    app.run()