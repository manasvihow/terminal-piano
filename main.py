import os
import time
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.dom import NoMatches
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, Static, Switch

# This setup can be at the top
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
from fluidsynth import Synth
load_dotenv()


# Your data can be at the top level
NOTE_TO_MIDI = {
    "C3": 48, "C#3": 49, "D3": 50, "D#3": 51, "E3": 52,
    "F3": 53, "F#3": 54, "G3": 55, "G#3": 56, "A3": 57,
    "A#3": 58, "B3": 59, "C4": 60, "C#4": 61, "D4": 62,
    "D#4": 63, "E4": 64, "F4": 65, "F#4": 66, "G4": 67,
    "G#4": 68, "A4": 69, "A#4": 70, "B4": 71, "C5": 72, "C#5": 73,
}
TWINKLE_TWINKLE = [
    (0.0, "C4", 0.4), (0.5, "C4", 0.4), (1.0, "G4", 0.4), (1.5, "G4", 0.4),
    (2.0, "A4", 0.4), (2.5, "A4", 0.4), (3.0, "G4", 0.9),
    (4.0, "F4", 0.4), (4.5, "F4", 0.4), (5.0, "E4", 0.4), (5.5, "E4", 0.4),
    (6.0, "D4", 0.4), (6.5, "D4", 0.4), (7.0, "C4", 0.9),
]


class FallingNote(Static):
    """A widget representing a single falling note."""
    def __init__(self, note: str, duration: float, **kwargs) -> None:
        super().__init__("", **kwargs)
        self.note = note
        self.duration = duration
        self.styles.height = int(duration * 20)


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
        self.app.handle_player_note_press(self.note)


class PianoApp(App):
    """A piano tiles style game."""
    CSS_PATH = "main.tcss"
    KEY_MAP = {
        'a': "C3", 'w': "C#3", 's': "D3", 'e': "D#3", 'd': "E3",
        'f': "F3", 't': "F#3", 'g': "G3", 'y': "G#3", 'h': "A3",
        'u': "A#3", 'j': "B3", 'k': "C4", 'o': "C#4", 'l': "D4",
        'p': "D#4", ';': "E4", "'": "F4", '[': "F#4", ']': "G4",
        '\\': "G#4",
    }
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_song", "Start / Pause"),
        ("r", "reset_song", "Reset"),
    ]

    def __init__(self):
        super().__init__()
        self.fs = Synth()
        self.fs.start(driver='coreaudio')
        sfid = self.fs.sfload("assets/sounds/GeneralUser.sf2")
        self.fs.program_select(0, sfid, 0, 0)

        self.song_data = TWINKLE_TWINKLE
        self.key_positions = {}
        self.fall_speed = 5.0
        # Controller 64 is the sustain pedal, value 127 is "on".
        self.fs.cc(0, 64, 127)
        
        # --- NEW: Game state variables, including score ---
        self.score = 0
        self.is_playing = False
        self.next_note_index = 0
        self.start_time = 0.0
        self.paused_time = 0.0

    def reset_song(self):
        """Resets the game to its initial state."""
        self.is_playing = False
        self.next_note_index = 0
        self.start_time = 0.0
        self.paused_time = 0.0
        self.score = 0
        if self.is_mounted:
            for note in self.query(FallingNote):
                note.remove()
            self.update_score_display()
            self.query_one(Header).title = "Piano Game"

    def update_score_display(self):
        """Helper to update the score in the header."""
        self.query_one(Header).sub_title = f"Score: {self.score}"

    def on_mount(self) -> None:
        self.reset_song()
        self.call_after_refresh(self.map_key_positions)
        self.set_interval(1 / 60, self.update_game)

    def map_key_positions(self) -> None:
        piano_container_x = self.query_one("#piano-container").region.x
        for key_widget in self.query(PianoKey):
            note_id = key_widget.note.replace("#", "-sharp-")
            relative_x = key_widget.region.x - piano_container_x
            self.key_positions[note_id] = relative_x

    def action_toggle_song(self):
        self.is_playing = not self.is_playing
        header = self.query_one(Header)
        if self.is_playing:
            header.title = "Piano Game - Playing..."
            self.start_time = time.monotonic() - self.paused_time if self.paused_time > 0 else time.monotonic()
        else:
            header.title = "Piano Game - Paused"
            self.paused_time = time.monotonic() - self.start_time

    def action_reset_song(self):
        self.reset_song()

    def on_key(self, event: Key) -> None:
        """Handles all player keyboard input."""
        if event.key in self.KEY_MAP:
            self.handle_player_note_press(self.KEY_MAP[event.key])

    def spawn_note(self, note_data: tuple):
        _start_time, note_name, duration = note_data
        note_id = note_name.replace("#", "-sharp-")
        new_note = FallingNote(note=note_name, duration=duration)
        new_note.add_class("black-note" if "#" in note_name else "white-note")
        note_area = self.query_one("#note-area")
        note_area.mount(new_note)
        key_offset = self.key_positions.get(note_id, 0)
        new_note.styles.offset = (key_offset, 0)
        
    def update_game(self):
        if not self.is_playing:
            return

        # Spawn notes as before
        current_time_in_song = time.monotonic() - self.start_time
        if self.next_note_index < len(self.song_data):
            next_note_data = self.song_data[self.next_note_index]
            if current_time_in_song >= next_note_data[0]:
                self.spawn_note(next_note_data)
                self.next_note_index += 1
                if self.next_note_index >= len(self.song_data):
                    self.set_timer(5.0, self.reset_song)

        # --- UPDATED: Game logic for MISSES ---
        # A note is a "miss" if it falls off the screen without being played.
        note_area_height = self.query_one("#note-area").content_region.height
        for note in self.query(FallingNote):
            new_offset_y = note.styles.offset.y.value + (self.fall_speed / 60)
            note.styles.offset = (note.styles.offset.x.value, new_offset_y)
            
            # If a note falls past the bottom, it's a miss.
            if note.styles.offset.y.value >= note_area_height:
                self.score -= 5 # Penalty for missing
                self.update_score_display()
                note.remove()

    # --- REMOVED: The auto-playing 'handle_visualizer_note_press' is gone ---

    # --- UPDATED: This is now the main game logic for HITS ---
    def handle_player_note_press(self, note: str):
        """Called by on_key or on_click when the PLAYER presses a key."""
        midi_note = NOTE_TO_MIDI.get(note)
        if midi_note is None: return

        # Play the sound regardless of hit or miss
        self.fs.noteon(0, midi_note, 100)
        self.set_timer(0.4, lambda n=midi_note: self.fs.noteoff(0, n))

        # Flash the piano key
        note_id = note.replace("#", "-sharp-")
        try:
            key_widget = self.query_one(f"#{note_id}", PianoKey)
            key_widget.add_class("key--pressed")
            self.set_timer(0.2, lambda k=key_widget: k.remove_class("key--pressed"))
        except NoMatches: pass

        # --- NEW: Check if this key press was a successful "hit" ---
        note_area_height = self.query_one("#note-area").content_region.height
        hit_zone_height = 10 # How generous the timing is

        # Search for a falling note that matches the key pressed
        for falling_note in self.query(FallingNote):
            if falling_note.note == note:
                # Check if the note is in the hit zone at the bottom
                note_y = falling_note.styles.offset.y.value
                if note_area_height - hit_zone_height <= note_y <= note_area_height:
                    self.score += 10 # Reward for a hit!
                    self.update_score_display()
                    falling_note.remove() # Remove the successfully hit note
                    return # Exit after the first successful hit

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="centering-grid"):
            yield Static()
            with Container(id="game-area"):
                yield Container(id="note-area")
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
            yield Static()
        yield Footer()


if __name__ == "__main__":
    app = PianoApp()
    app.run()