from typing import Iterable
from textual.widgets import Static

from toad.menus import MenuItem


class Note(Static):
    def get_block_menu(self) -> Iterable[MenuItem]:
        yield MenuItem("Hello", "block.hello('HI')")
        yield MenuItem("World!", "app.notify('hello')")
        yield MenuItem("A longer menu option", "app.notify('hello')")

    def get_block_content(self) -> str | None:
        return str(self.render())

    def action_hello(self, message: str) -> None:
        self.notify(message, severity="warning")
