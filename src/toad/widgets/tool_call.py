from textual.app import ComposeResult
from textual import containers
from textual.widgets import Static, Markdown
from textual.reactive import var, Initialize

from toad.acp import protocol


class TextContent(Static):
    DEFAULT_CSS = """
    ContentText 
    {
        height: auto;
    }
    """


class ToolCall(Static):
    DEFAULT_CLASSES = "block"


class ToolCallContent(containers.VerticalGroup):
    DEFAULT_CSS = """
    ToolCalLContent {
        layout: stream;
        height: auto;
    }

    """

    def __init__(
        self,
        tool_call: protocol.ToolCall,
        *,
        id: str | None,
        classes: str | None = None,
    ) -> None:
        self._tool_call = tool_call
        super().__init__(id=id, classes=classes)

    @property
    def tool_call(self) -> protocol.ToolCall:
        return self._tool_call

    def compose(self) -> ComposeResult:
        content = self.tool_call.get("content", None) or []
        for content in content:
            match content:
                case {"type": "text", "text": text}:
                    yield TextContent(text, markup=False)
