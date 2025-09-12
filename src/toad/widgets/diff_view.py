from __future__ import annotations

from rich.style import Style as RichStyle

from textual.app import ComposeResult
from textual.content import Content, Span
from textual.geometry import Size
from textual import highlight
from textual.css.styles import RulesMap
from textual._segment_tools import line_pad
from textual.strip import Strip
from textual.style import Style
from textual.reactive import reactive, var
from textual.visual import Visual, RenderOptions
from textual.widget import Widget
from textual.widgets import Static
from textual import containers

import difflib


class DiffScrollContainer(containers.HorizontalGroup):
    scroll_link: var[Widget | None] = var(None)
    DEFAULT_CSS = """
    DiffScrollContainer {
        overflow: scroll hidden;
        scrollbar-size: 0 0;
    }
    """

    def watch_scroll_x(self, old_value: float, new_value: float) -> None:
        super().watch_scroll_x(old_value, new_value)
        if self.scroll_link:
            self.scroll_link.scroll_x = new_value


class LineContent(Visual):
    def __init__(
        self,
        code_lines: list[Content],
        line_styles: list[str],
        width: int | None = None,
    ) -> None:
        self.code_lines = code_lines
        self.line_styles = line_styles
        self._width = width

    # def render_strips(
    #     self, width: int, height: int | None, style: Style, options: RenderOptions
    # ) -> list[Strip]:
    #     strips = super().render_strips(width, height, style, options)
    #     strips = [
    #         strip.adjust_cell_length(
    #             width, RichStyle.from_color(None, strip._segments[-1].style.bgcolor)
    #         )
    #         for strip in strips
    #     ]
    #     return strips

    def render_strips(
        self, width: int, height: int | None, style: Style, options: RenderOptions
    ) -> list[Strip]:
        strips: list[Strip] = []
        for line, color in zip(self.code_lines, self.line_styles):
            if line.cell_length < width:
                line = line.extend_right(width - line.cell_length)
            line = line.stylize_before(color).stylize_before(style)

            # TODO: rich_style_with_offsets needed to make content selectable
            strips.append(Strip(line.render_segments(), line.cell_length))
        return strips

    def get_optimal_width(self, rules: RulesMap, container_width: int) -> int:
        if self._width is not None:
            return self._width
        return max(line.cell_length for line in self.code_lines)

    def get_minimal_width(self, rules: RulesMap) -> int:
        return 1

    def get_height(self, rules: RulesMap, width: int) -> int:
        return len(self.code_lines)


class LineAnnotations(Widget):
    DEFAULT_CSS = """
    LineAnnotations {
        width: auto;
        height: auto;                
    }
    """
    numbers: reactive[list[Content]] = reactive(list)
    left_pad: reactive[int] = reactive(0)
    right_pad: reactive[int] = reactive(0)

    def __init__(
        self,
        numbers: list[Content],
        *,
        left_pad=0,
        right_pad=0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

        self.set_reactive(LineAnnotations.left_pad, left_pad)
        self.set_reactive(LineAnnotations.right_pad, right_pad)
        self.numbers = numbers

    @property
    def total_width(self) -> int:
        return self.left_pad + self.number_width + self.right_pad

    def get_content_width(self, container: Size, viewport: Size) -> int:
        return self.total_width

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return len(self.numbers)

    @property
    def number_width(self) -> int:
        numbers = self.numbers
        if numbers:
            return max(number.cell_length for number in numbers)
        else:
            return 0

    def render_line(self, y: int) -> Strip:
        width = self.total_width
        visual_style = self.visual_style
        rich_style = visual_style.rich_style
        try:
            number = self.numbers[y]
        except IndexError:
            number = Content.empty()

        strip = Strip(
            line_pad(
                number.render_segments(visual_style),
                self.left_pad,
                self.right_pad,
                rich_style,
            ),
            cell_length=number.cell_length + self.left_pad + self.right_pad,
        )
        strip = strip.adjust_cell_length(width, rich_style)
        return strip


class DiffCode(Static):
    DEFAULT_CSS = """
    DiffCode {
        width: auto;        
        height: auto;
        min-width: 1fr;
    }
    """


def fill_lists[T](list_a: list[T], list_b: list[T], fill_value: T) -> None:
    """Make two lists the same size by extending the smaller with a fill value.

    Args:
        list_a: The first list.
        list_b: The second list.
        fill_value: Value used to extend a list.

    """
    a_length = len(list_a)
    b_length = len(list_b)
    if a_length != b_length:
        if a_length > b_length:
            list_b.extend([fill_value] * (a_length - b_length))
        elif b_length > a_length:
            list_a.extend([fill_value] * (b_length - a_length))


class DiffView(containers.HorizontalGroup):
    code_before: reactive[str] = reactive("")
    code_after: reactive[str] = reactive("")
    path1: reactive[str] = reactive("")
    path2: reactive[str] = reactive("")
    language: reactive[str | None] = reactive(None)
    split: reactive[bool] = reactive(True, recompose=True)

    DEFAULT_CSS = """
    DiffView {
        width: 1fr;
        height: auto;
    }
    """

    NUMBER_STYLES = {
        "+": "$foreground 80% on $success 30%",
        "-": "$foreground 80% on $error 30%",
        " ": "$foreground 40%",
    }
    LINE_STYLES = {
        "+": "on $success 15%",
        "-": "on $error 15%",
        " ": "",
    }

    def __init__(
        self,
        path1: str,
        path2: str,
        code_before: str,
        code_after: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.set_reactive(DiffView.path1, path1)
        self.set_reactive(DiffView.path2, path2)
        self.set_reactive(DiffView.code_before, code_before)
        self.set_reactive(DiffView.code_after, code_after)

    def compose(self) -> ComposeResult:
        if self.split:
            yield from self.compose_split()
        else:
            yield from self.compose_unified()

    def compose_unified(self) -> ComposeResult:
        language1 = highlight.guess_language(self.code_before, self.path1)
        language2 = highlight.guess_language(self.code_after, self.path2)

        text_lines_a = self.code_before.splitlines()
        text_lines_b = self.code_after.splitlines()

        lines_a = highlight.highlight(
            "\n".join(text_lines_a), language=language1, path=self.path1
        ).split("\n")
        lines_b = highlight.highlight(
            "\n".join(text_lines_b), language=language2, path=self.path2
        ).split("\n")

        line_numbers_a: list[int | None] = []
        line_numbers_b: list[int | None] = []
        annotations: list[str] = []
        code_lines: list[Content] = []

        for group in difflib.SequenceMatcher(
            None, text_lines_a, text_lines_b
        ).get_grouped_opcodes():
            for tag, i1, i2, j1, j2 in group:
                if tag == "equal":
                    for line_offset, line in enumerate(lines_a[i1:i2], 1):
                        annotations.append(" ")
                        line_numbers_a.append(i1 + line_offset)
                        line_numbers_b.append(j1 + line_offset)
                        code_lines.append(line)
                    continue
                if tag in {"replace", "delete"}:
                    for line_number, line in enumerate(lines_a[i1:i2], i1 + 1):
                        annotations.append("-")
                        line_numbers_a.append(line_number)
                        line_numbers_b.append(None)
                        code_lines.append(line)
                if tag in {"replace", "insert"}:
                    for line_number, line in enumerate(lines_b[j1:j2], j1 + 1):
                        annotations.append("+")
                        line_numbers_a.append(None)
                        line_numbers_b.append(line_number)
                        code_lines.append(line)

        NUMBER_STYLES = self.NUMBER_STYLES
        LINE_STYLES = self.LINE_STYLES

        line_number_width = max(
            len("" if line_no is None else str(line_no))
            for line_no in (line_numbers_a + line_numbers_b)
        )

        yield LineAnnotations(
            [
                (
                    Content(f" {' ' * line_number_width} ")
                    if line_no is None
                    else Content(f" {line_no:>{line_number_width}} ")
                ).stylize(NUMBER_STYLES[annotation])
                for line_no, annotation in zip(line_numbers_a, annotations)
            ]
        )

        yield LineAnnotations(
            [
                (
                    Content(f" {' ' * line_number_width} ")
                    if line_no is None
                    else Content(f" {line_no:>{line_number_width}} ")
                ).stylize(NUMBER_STYLES[annotation])
                for line_no, annotation in zip(line_numbers_b, annotations)
            ]
        )

        yield LineAnnotations(
            [
                (Content(f" {annotation} "))
                .stylize(LINE_STYLES[annotation])
                .stylize("bold")
                for annotation in annotations
            ]
        )
        code_line_styles = [LINE_STYLES[annotation] for annotation in annotations]
        with DiffScrollContainer():
            yield DiffCode(LineContent(code_lines, code_line_styles))

    def compose_split(self) -> ComposeResult:
        language1 = highlight.guess_language(self.code_before, self.path1)
        language2 = highlight.guess_language(self.code_after, self.path2)

        text_lines_a = self.code_before.splitlines()
        text_lines_b = self.code_after.splitlines()

        lines_a = highlight.highlight(
            "\n".join(text_lines_a), language=language1, path=self.path1
        ).split("\n")
        lines_b = highlight.highlight(
            "\n".join(text_lines_b), language=language2, path=self.path2
        ).split("\n")

        line_width = max(line.cell_length for line in lines_a + lines_b)

        line_numbers_a: list[int | None] = []
        line_numbers_b: list[int | None] = []
        annotations_a: list[str] = []
        annotations_b: list[str] = []
        code_lines_a: list[Content] = []
        code_lines_b: list[Content] = []

        for group in difflib.SequenceMatcher(
            None, text_lines_a, text_lines_b
        ).get_grouped_opcodes():
            for tag, i1, i2, j1, j2 in group:
                if tag == "equal":
                    for line_offset, line in enumerate(lines_a[i1:i2], 1):
                        annotations_a.append(" ")
                        annotations_b.append(" ")
                        line_numbers_a.append(i1 + line_offset)
                        line_numbers_b.append(j1 + line_offset)
                        code_lines_a.append(line)
                        code_lines_b.append(line)
                    continue
                if tag in {"replace", "delete"}:
                    for line_number, line in enumerate(lines_a[i1:i2], i1 + 1):
                        annotations_a.append("-")
                        line_numbers_a.append(line_number)
                        code_lines_a.append(line)
                if tag in {"replace", "insert"}:
                    for line_number, line in enumerate(lines_b[j1:j2], j1 + 1):
                        annotations_b.append("+")
                        line_numbers_b.append(line_number)
                        code_lines_b.append(line)
                fill_lists(code_lines_a, code_lines_b, Content.empty())
                fill_lists(annotations_a, annotations_b, " ")
                fill_lists(line_numbers_a, line_numbers_b, None)

        NUMBER_STYLES_A = self.NUMBER_STYLES.copy()
        NUMBER_STYLES_A["+"] = ""

        NUMBER_STYLES_B = self.NUMBER_STYLES.copy()
        NUMBER_STYLES_B["-"] = ""

        LINE_STYLES_A = self.LINE_STYLES.copy()
        LINE_STYLES_A["+"] = ""

        LINE_STYLES_B = self.LINE_STYLES.copy()
        LINE_STYLES_B["-"] = ""

        line_number_width = max(
            len("" if line_no is None else str(line_no))
            for line_no in (line_numbers_a + line_numbers_b)
        )

        yield LineAnnotations(
            [
                (
                    Content(f" {' ' * line_number_width} ")
                    if line_no is None
                    else Content(f" {line_no:>{line_number_width}} ")
                ).stylize(NUMBER_STYLES_A[annotation])
                for line_no, annotation in zip(line_numbers_a, annotations_a)
            ]
        )
        yield LineAnnotations(
            [
                (Content(f" {annotation} " if annotation != "+" else "   "))
                .stylize(LINE_STYLES_A[annotation])
                .stylize("bold")
                for annotation in annotations_a
            ]
        )

        code_line_styles = [LINE_STYLES_A[annotation] for annotation in annotations_a]
        with DiffScrollContainer() as scroll_container_a:
            yield DiffCode(
                LineContent(code_lines_a, code_line_styles, width=line_width)
            )

        yield LineAnnotations(
            [
                (
                    Content(f" {' ' * line_number_width} ")
                    if line_no is None
                    else Content(f" {line_no:>{line_number_width}} ")
                ).stylize(NUMBER_STYLES_B[annotation])
                for line_no, annotation in zip(line_numbers_b, annotations_b)
            ]
        )

        yield LineAnnotations(
            [
                (Content(f" {annotation} " if annotation != "-" else "   "))
                .stylize(LINE_STYLES_B[annotation])
                .stylize("bold")
                for annotation in annotations_b
            ]
        )

        code_line_styles = [LINE_STYLES_B[annotation] for annotation in annotations_b]
        with DiffScrollContainer() as scroll_container_b:
            yield DiffCode(
                LineContent(code_lines_b, code_line_styles, width=line_width)
            )

        scroll_container_a.scroll_link = scroll_container_b
        scroll_container_b.scroll_link = scroll_container_a


if __name__ == "__main__":
    SOURCE1 = '''\
def loop_first(values: Iterable[T]) -> Iterable[tuple[bool, T]]:
    """Iterate and generate a tuple with a flag for first value."""
    iter_values = iter(values)
    try:
        value = next(iter_values)
    except StopIteration:
        return
    yield True, value
    for value in iter_values:
        yield False, value


def loop_first_last(values: Iterable[T]) -> Iterable[tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value

'''

    SOURCE2 = '''\
def loop_first(values: Iterable[T]) -> Iterable[tuple[bool, T]]:
    """Iterate and generate a tuple with a flag for first value.
    
    Args:
        values: iterables of values.

    Returns:
        Iterable of a boolean to indicate first value, and a value from the iterable.
    """
    iter_values = iter(values)
    try:
        value = next(iter_values)
    except StopIteration:
        return
    yield True, value
    for value in iter_values:
        yield False, value


def loop_last(values: Iterable[T]) -> Iterable[tuple[bool, T]]:
    """Iterate and generate a tuple with a flag for last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    for value in iter_values:
        yield False, previous_value
        previous_value = value
    yield True, previous_value


def loop_first_last(values: Iterable[ValueType]) -> Iterable[tuple[bool, bool, ValueType]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True

'''
    from textual.app import App

    class DiffApp(App):
        BINDINGS = [("space", "split", "Toggle split")]

        def compose(self) -> ComposeResult:
            yield DiffView("foo.py", "foo.py", SOURCE1, SOURCE2)

        def action_split(self) -> None:
            self.query_one(DiffView).split = not self.query_one(DiffView).split

    app = DiffApp()
    app.run()
