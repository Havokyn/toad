from __future__ import annotations

from typing import ClassVar
from time import monotonic

from textual.reactive import var
from textual.content import Content
from textual.style import Style
from textual.widgets import Static


class FutureText(Static):
    """Text which appears one letter at time, like the movies."""

    DEFAULT_CSS = """
    FutureText {
        width: auto;
        height: 1;
        text-wrap: nowrap;
        text-align: center;
        &>.future-text--cursor {
            color: $primary;
        }
    }
    """

    COMPONENT_CLASSES = {"future-text--cursor"}

    BARS: ClassVar[list[str]] = ["▉", "▊", "▋", "▌", "▍", "▎", "▏", " "]
    text_offset = var(0)

    def __init__(
        self,
        text_list: list[Content],
        *,
        speed: float = 16.0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        self.text_list = text_list
        self.speed = speed
        self.start_time = monotonic()
        super().__init__(name=name, id=id, classes=classes)

    @property
    def text(self) -> Content:
        return self.text_list[self.text_offset % len(self.text_list)]

    @property
    def time(self) -> float:
        return monotonic() - self.start_time

    def on_mount(self) -> None:
        self.start_time = monotonic()

        self.set_interval(1 / 60, self._update_text)

    def _update_text(self) -> None:
        text = self.text + " "
        speed_time = self.time * self.speed
        progress, fractional_progress = divmod(speed_time, 1)
        end = progress >= len(text)
        cursor_progress = 0 if end else int(fractional_progress * 8)
        text = text[: round(progress)]

        bar_character = self.BARS[7 - cursor_progress]

        cursor_style = self.get_component_styles("future-text--cursor")
        cursor_style = Style(foreground=cursor_style.color)
        reverse_cursor_style = cursor_style + Style(reverse=True)

        text = Content.assemble(
            text,
            (bar_character, reverse_cursor_style),
            (bar_character, cursor_style),
            " " * (len(self.text) - len(text) + 1),
        )
        self.update(text, layout=False)

        if progress > len(text) + 10 * 5:
            self.text_offset += 1
            self.start_time = monotonic()


if __name__ == "__main__":
    from textual.app import App, ComposeResult

    TEXT = [Content("Thinking..."), Content("Working hard..."), Content("Nearly there")]

    class TextApp(App):
        CSS = """
        Screen {
            padding: 2 4;
            FutureText {
                width: auto;
                max-width: 1fr;
                height: auto;
               
            }
        }
        """

        def compose(self) -> ComposeResult:
            yield FutureText(TEXT)

    TextApp().run()
