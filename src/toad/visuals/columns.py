from __future__ import annotations

from itertools import accumulate
import operator
from typing import Literal
from fractions import Fraction

from rich.segment import Segment

from textual.content import Content
from textual.visual import Visual, RenderOptions
from textual.strip import Strip
from textual.style import Style

from toad._loop import loop_last


class Row(Visual):
    def __init__(self, columns: Columns, row_index: int) -> None:
        self.columns = columns
        self.row_index = row_index

    def render_strips(
        self, width: int, height: int | None, style: Style, options: RenderOptions
    ) -> list[Strip]:
        return []


class Columns:
    """Renders columns of Content."""

    def __init__(
        self,
        *columns: Literal["auto", "flex"],
        gutter: int = 1,
        style: Style | str = "",
    ) -> None:
        self.columns = columns
        self.gutter = gutter
        self.style = style
        self.rows: list[list[Content]] = []

        self.last_render_parameters: tuple[int, Style] = (-1, Style())

    def add_row(self, *cells: Content | str) -> None:
        assert len(cells) == len(self.columns)
        new_cells = [
            cell if isinstance(cell, Content) else Content(cell) for cell in cells
        ]
        self.rows.append(new_cells)

    def _render(self, render_width: int, style: Style) -> list[Row]:
        gutter_width = (len(self.columns) - 1) * self.gutter
        widths: list[int | None] = []

        for index, column in enumerate(self.columns):
            if column == "auto":
                widths.append(max(row[index].cell_length for row in self.rows))
            else:
                widths.append(None)

        if any(width is None for width in widths):
            remaining_width = Fraction(render_width - gutter_width)
            if remaining_width <= 0:
                widths = [width or 0 for width in widths]
            else:
                remaining_count = sum(1 for width in widths if width is None)
                cell_width = remaining_width / remaining_count

                distribute = map(
                    int,
                    accumulate(
                        [cell_width] * remaining_count, operator.add, initial=cell_width
                    ),
                )
                iter_distribute = iter(distribute)
                for index, column_width in enumerate(widths.copy()):
                    if column_width is None:
                        widths[index] = int(next(iter_distribute))

        column_renders: list[list[list[Segment]]] = []
        for row in self.rows:
            for content_width, content in zip(widths, row):
                assert content_width is not None
                segments = [
                    line.truncate(content_width, pad=True).render_segments(style)
                    for line in content.wrap(content_width)
                ]

                column_renders.append(segments)

        height = max(len(lines) for lines in column_renders)
        rich_style = style.rich_style
        for width, lines in zip(widths, column_renders):
            assert width is not None
            while len(lines) < height:
                lines.append([Segment(" " * width, rich_style)])

        from rich import print

        gutter = Segment(" " * self.gutter, rich_style)
        strips: list[Strip] = []
        for line_no in range(height):
            strip_segments: list[Segment] = []
            for last, column in loop_last(column_renders):
                strip_segments.extend(column[line_no])
                if not last and gutter:
                    strip_segments.append(gutter)
            strips.append(Strip(strip_segments, render_width))
        print(strips)


if __name__ == "__main__":
    from rich import traceback

    traceback.install(show_locals=True)

    columns = Columns("auto", "flex")
    columns.add_row("foo", "hello world" * 20)
    print(columns.columns)
    columns._render(30, Style())
