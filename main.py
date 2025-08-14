# main.py

import os
import time
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.dom import NoMatches
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, Static, Switch, Select
from textual.css.query import NoMatches as NoMatchesError # For older Textual versions

# This setup can be at the top
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
from fluidsynth import Synth

# The list of instruments you provided
GENERAL_MIDI_INSTRUMENTS = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavi", "Celesta", "Glockenspiel",
    "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer", "Drawbar Organ",
    "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ", "Accordion", "Harmonica",
    "Tango Accordion", "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)",
    "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar",
    "Guitar Harmonics", "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)",
    "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2", "Violin",
    "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp",
    "Timpani", "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
    "Choir Aahs", "Voice Oohs", "Synth Choir", "Orchestra Hit", "Trumpet", "Trombone", "Tuba",
    "Muted Trumpet", "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2", "Soprano Sax",
    "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet",
    "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle",
    "Ocarina", "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)",
    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)",
    "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)", "FX 1 (rain)", "FX 2 (soundtrack)",
    "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)",
    "FX 7 (echoes)", "FX 8 (sci-fi)", "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba",
    "Bagpipe", "Fiddle", "Shanai", "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock",
    "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal", "Guitar Fret Noise",
    "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot"
]
NOTE_TO_MIDI = {
    "C3": 48, "C#3": 49, "D3": 50, "D#3": 51, "E3": 52, "F3": 53, "F#3": 54, "G3": 55,
    "G#3": 56, "A3": 57, "A#3": 58, "B3": 59, "C4": 60, "C#4": 61, "D4": 62, "D#4": 63,
    "E4": 64, "F4": 65, "F#4": 66, "G4": 67, "G#4": 68, "A4": 69, "A#4": 70, "B4": 71,
    "C5": 72, "C#5": 73, "D5": 74, "D#5": 75, "E5": 76, "F5": 77, "F#5": 78, "G5": 79,
    "G#5": 80, "A5": 81, "A#5": 82, "B5": 83, "C6": 84, "C#6": 85, "D6": 86, "D#6": 87,
    "E6": 88, "F6": 89, "F#6": 90, "G6": 91, "G#6": 92, "A6": 93, "A#6": 94, "B6": 95, "C7": 96
}

# --- Copied from your provided code ---
_NAKED_SLIDER = "╷         ╷         ╷\n├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤\n╵         ╵         ⵨"
class Slider(Static):
    position = reactive(0)
    def __init__(self, position=0, **kwargs):
        super().__init__(_NAKED_SLIDER, **kwargs)
        self.position = position
    def on_mount(self) -> None:
        self.watch_position(self.position)
    def watch_position(self, position: int) -> None:
        self.styles.padding = (0, 0, 0, position)
class LabeledSlider(Static):
    value = reactive(0)
    def __init__(self, label, value=100, value_range=(0, 127), id=""):
        super().__init__(id=id)
        self.label = label
        self.min_value, self.max_value = value_range
        self.value = value
    def compose(self) -> ComposeResult:
        initial_pos = self.value * 20 // (self.max_value - self.min_value)
        yield Label(self.label)
        yield Slider(position=initial_pos)
    def on_key(self, event: Key) -> None:
        slider = self.query_one(Slider)
        if event.key == "left":
            slider.position = max(0, slider.position - 1)
        elif event.key == "right":
            slider.position = min(20, slider.position + 1)
        self.value = slider.position * (self.max_value - self.min_value) // 20
# --- End of copied code ---


class PianoKey(Static):
    # This class is unchanged
    def __init__(self, note: str, keyboard_key: str, is_black: bool, **kwargs) -> None:
        super().__init__(keyboard_key, **kwargs)
        self.note = note
        self.keyboard_key = keyboard_key
        self.is_black = is_black
        self.add_class("key")
        self.add_class("key--black" if is_black else "key--white")
    def on_click(self) -> None:
        self.app.handle_player_note_press(self.note)


class PianoApp(App):
    """An interactive terminal piano with more options."""
    CSS_PATH = "main.tcss"
    KEY_MAP = {
        'z': "C3", 'x': "D3", 'c': "E3", 'v': "F3", 'b': "G3", 'n': "A3", 'm': "B3",
        'a': "C4", 's': "D4", 'd': "E4", 'f': "F4", 'g': "G4", 'h': "A4", 'j': "B4",
        '2': "C#3", '3': "D#3", '5': "F#3", '6': "G#3", '7': "A#3",
        'q': "C#4", 'w': "D#4", 'r': "F#4", 't': "G#4", 'y': "A#4",
    }
    # --- UPDATED: Added Tab binding for sustain ---
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "toggle_sustain", "Sustain"),
    ]

    sustain_on = reactive(False)

    def __init__(self):
        super().__init__()
        self.fs = Synth()
        self.fs.start(driver='coreaudio')
        self.sfid = self.fs.sfload("assets/sounds/GeneralUser.sf2")
        self.fs.program_select(0, self.sfid, 0, 0)
        self.fs.cc(0, 7, 100) # Set default volume to 100

    # In main.py, inside the PianoApp class

    def watch_sustain_on(self, sustain_on: bool) -> None:
        """Called automatically when sustain_on changes."""
        # We are no longer telling the synth about sustain.
        # We only care when sustain is turned OFF, so we can stop all notes.
        if not sustain_on:
            self.fs.all_notes_off(0)

    # --- NEW: Event handlers for the new controls ---
    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "sustain-switch": self.sustain_on = event.value
    
    # In main.py
    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "instrument-select":
            program_id = event.value
            
            # --- FIX: If the blank prompt is selected, default to piano (ID 0) ---
            if program_id is Select.BLANK:
                program_id = 0
            
            self.fs.program_select(0, self.sfid, 0, program_id)
            self.fs.all_notes_off(0)
        

    def watch_labeled_slider_value(self, new_value: int) -> None:
        # This is a special watcher that triggers when ANY LabeledSlider value changes.
        # We find out which one by looking at the widget with the new value.
        slider = self.get_widget_by_value(LabeledSlider, "value", new_value)
        if slider.id == "volume-slider":
            self.fs.cc(0, 7, new_value)

    # --- NEW: Action for the Tab key binding ---
    def action_toggle_sustain(self) -> None:
        self.query_one("#sustain-switch", Switch).toggle()

    def on_key(self, event: Key) -> None:
        # --- UPDATED: Stop Tab key's default focus-switching behavior ---
        if event.key == "tab":
            event.stop()
            return
        if event.key in self.KEY_MAP:
            self.handle_player_note_press(self.KEY_MAP[event.key])

    # In main.py, inside the PianoApp class

    # In main.py, inside the PianoApp class

    def handle_player_note_press(self, note: str):
        """Plays a note when the user presses a key or clicks."""
        midi_note = NOTE_TO_MIDI.get(note)
        if midi_note is None: return

        # --- FIX #2: Immediately stop the note before playing it again ---
        self.fs.noteoff(0, midi_note) 
        
        self.fs.noteon(0, midi_note, 100)
        
        # --- FIX #3: Always schedule the note to turn off, but vary the duration ---
        duration = 2.0 if self.sustain_on else 0.5
        self.set_timer(duration, lambda n=midi_note: self.fs.noteoff(0, n))

        # Visual flash for the key (this logic is unchanged)
        note_id = note.replace("#", "-sharp-")
        try:
            key_widget = self.query_one(f"#{note_id}", PianoKey)
            key_widget.add_class("key--pressed")
            self.set_timer(0.2, lambda k=key_widget: k.remove_class("key--pressed"))
        except (NoMatches, NoMatchesError): pass

    def compose(self) -> ComposeResult:
        yield Header()
        
        # --- UPDATED: Adding all new controls here ---
        with Horizontal(id="controls-container"):
            # Sustain Switch
            yield Label("Sustain:")
            yield Switch(id="sustain-switch")
            
            # Instrument Select
            instrument_options = [(name, i) for i, name in enumerate(GENERAL_MIDI_INSTRUMENTS)]
            yield Select(instrument_options, id="instrument-select", prompt="Piano")

            # Volume Slider
            yield LabeledSlider("Volume:", id="volume-slider")

        # The rest of the layout is unchanged
        with Container(id="centering-grid"):
            with Container(id="piano-area"):
                with Container(id="piano-container"):
                    for note in NOTE_TO_MIDI:
                        if "#" not in note:
                            key_char = next((k for k, v in self.KEY_MAP.items() if v == note), "")
                            note_id = note.replace("#", "-sharp-")
                            yield PianoKey(note, key_char, is_black=False, id=note_id)
                    for note in NOTE_TO_MIDI:
                        if "#" in note:
                            key_char = next((k for k, v in self.KEY_MAP.items() if v == note), "")
                            note_id = note.replace("#", "-sharp-")
                            yield PianoKey(note, key_char, is_black=True, id=note_id)
        yield Footer()

if __name__ == "__main__":
    app = PianoApp()
    app.run()