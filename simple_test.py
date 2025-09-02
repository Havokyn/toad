from rich import print
from rich.console import Console

console = Console()
console.print("[red]0123456789[/red] " * 10, soft_wrap=True)
