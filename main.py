from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

class PianoApp(App):
    """A terminal piano application."""

    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

if __name__ == "__main__":
    app = PianoApp()
    app.run()