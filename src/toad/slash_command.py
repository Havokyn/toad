from textual.content import Content


class SlashCommand:
    def __init__(self, command: str, help: str) -> None:
        self.command = command
        self.help = help

    def __str__(self) -> str:
        return self.command

    @property
    def content(self) -> Content:
        return Content.assemble(
            (self.command, "$text-success"), "\t", (self.help, "dim")
        )
