# main.py

from textual.app import App
from screens import SongSelectScreen

class PianoApp(App):
    """A piano visualizer application."""
    CSS_PATH = "main.tcss"



    def on_mount(self) -> None:
        """Start the app by showing the song selection screen."""
        self.push_screen(SongSelectScreen())

if __name__ == "__main__":
    app = PianoApp()
    app.run()