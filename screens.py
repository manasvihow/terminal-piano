# screens.py

import time
# In screens.py
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.dom import NoMatches
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Footer, Header, Select, Static

# Import our custom data and widgets
from songs import SONGS, NOTE_TO_MIDI
from widgets import FallingNote, PianoKey

# Note: The fluidsynth setup has moved into the GameScreen
from fluidsynth import Synth


class SongSelectScreen(Screen):
    """The first screen the user sees, for choosing a song."""

    # Use a custom action name
    BINDINGS = [
        ("q", "request_quit", "Quit"),
    ]

    # Add this new method to the class
    def action_request_quit(self) -> None:
        """Tell the main app to exit."""
        self.app.exit()



    def compose(self) -> ComposeResult:
        yield Header(show_clock=False, name="Select a Song")
        # The value of a selection is the song's title (the key in our SONGS dict)
        yield Select(
            [(title, title) for title in SONGS.keys()],
            prompt="Choose a song to play...",
        )
        yield Footer()

    def on_select_changed(self, event: Select.Changed) -> None:
        """When a song is selected, switch to the game screen."""
        self.app.push_screen(GameScreen(song_title=event.value))


class GameScreen(Screen):
    """The main game screen with the piano and falling notes."""

    # Using the same KEY_MAP and BINDINGS as before
    # In screens.py, inside the GameScreen class

    # In screens.py, inside the GameScreen class

    # --- FINAL: The definitive key map with your preferred white key layout ---
    KEY_MAP = {
        # --- White Keys ---
        # Bottom row (Octave 3)
        'z': "C3", 'x': "D3", 'c': "E3", 'v': "F3", 'b': "G3", 'n': "A3", 'm': "B3",
        # Middle row (Octave 4)
        'a': "C4", 's': "D4", 'd': "E4", 'f': "F4", 'g': "G4", 'h': "A4", 'j': "B4", 'k': "C5",

        # --- Black Keys ---
        # Number row (Octave 3)
        '2': "C#3", '3': "D#3", '5': "F#3", '6': "G#3", '7': "A#3",
        # Top letter row (Octave 4)
        'q': "C#4", 'w': "D#4", 'r': "F#4", 't': "G#4", 'y': "A#4",
    }
    # Change the 'q' binding back to the custom action
    BINDINGS = [
        ("q", "quit_game", "Back to Menu"),
        ("space", "toggle_song", "Play/Pause"),
        ("r", "reset_song", "Reset"),
    ]

    def __init__(self, song_title: str):
        super().__init__()
        self.song_title = song_title
        self.song_data = SONGS[song_title]

        self.fs = Synth()
        self.fs.start(driver='coreaudio')
        # Make sure your soundfont is in an 'assets/sounds' folder
        sfid = self.fs.sfload("assets/sounds/GeneralUser.sf2")
        self.fs.program_select(0, sfid, 0, 0)
        self.fs.cc(0, 64, 127) # Sustain always on

        self.key_positions = {}
        self.fall_speed = 12.0
        self.score = 0
        self.is_playing = False
        self.next_note_index = 0
        self.start_time = 0.0
        self.paused_time = 0.0

    def reset_song(self):
        self.is_playing = False
        self.next_note_index = 0
        self.start_time = 0.0
        self.paused_time = 0.0
        self.score = 0
        if self.is_mounted:
            for note in self.query(FallingNote):
                note.remove()
            self.update_score_display()
        self.query_one(Header).title = self.song_title

    def update_score_display(self):
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
    
    def action_quit_game(self) -> None:
        """Go back to the song selection screen."""
        self.app.pop_screen()

    # All other action_*, on_key, update_game, spawn_note, and handle_note_press
    # methods are the same as before, but with one change to spawn_note.

    def spawn_note(self, note_data: tuple):
        _start_time, notes_in_chord, duration = note_data
        # --- UPDATED: Loop through notes to handle chords ---
        for note_name in notes_in_chord:
            note_id = note_name.replace("#", "-sharp-")
            new_note = FallingNote(note=note_name, duration=duration)
            new_note.add_class("black-note" if "#" in note_name else "white-note")
            note_area = self.query_one("#note-area")
            note_area.mount(new_note)
            key_offset = self.key_positions.get(note_id, 0)
            new_note.styles.offset = (key_offset, 0)

    # (The rest of the game logic methods are unchanged from the last version)
    def action_toggle_song(self):
        self.is_playing = not self.is_playing
        header = self.query_one(Header)
        if self.is_playing:
            header.title = f"{self.song_title} - Playing..."
            self.start_time = time.monotonic() - self.paused_time if self.paused_time > 0 else time.monotonic()
        else:
            header.title = f"{self.song_title} - Paused"
            self.paused_time = time.monotonic() - self.start_time

    def action_reset_song(self):
        self.reset_song()

    def on_key(self, event: Key) -> None:
        if event.key in self.KEY_MAP:
            self.handle_player_note_press(self.KEY_MAP[event.key])

    def update_game(self):
        if not self.is_playing: return
        current_time_in_song = time.monotonic() - self.start_time
        if self.next_note_index < len(self.song_data):
            next_note_data = self.song_data[self.next_note_index]
            if current_time_in_song >= next_note_data[0]:
                self.spawn_note(next_note_data)
                self.next_note_index += 1
                if self.next_note_index >= len(self.song_data):
                    self.set_timer(5.0, self.reset_song)
        note_area_height = self.query_one("#note-area").content_region.height
        for note in self.query(FallingNote):
            new_offset_y = note.styles.offset.y.value + (self.fall_speed / 60)
            note.styles.offset = (note.styles.offset.x.value, new_offset_y)
            if note.styles.offset.y.value >= note_area_height:
                self.score -= 5
                self.update_score_display()
                note.remove()

    def handle_player_note_press(self, note: str):
        midi_note = NOTE_TO_MIDI.get(note)
        if midi_note is None: return
        self.fs.noteon(0, midi_note, 100)
        note_id = note.replace("#", "-sharp-")
        try:
            key_widget = self.query_one(f"#{note_id}", PianoKey)
            key_widget.add_class("key--pressed")
            self.set_timer(0.2, lambda k=key_widget: k.remove_class("key--pressed"))
        except NoMatches: pass
        note_area_height = self.query_one("#note-area").content_region.height
        hit_zone_height = 10
        for falling_note in self.query(FallingNote):
            if falling_note.note == note:
                note_y = falling_note.styles.offset.y.value
                if note_area_height - hit_zone_height <= note_y <= note_area_height:
                    self.score += 10
                    self.update_score_display()
                    falling_note.remove()
                    return

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