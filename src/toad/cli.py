import click
from toad.app import ToadApp


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Toad. The Batrachian AI."""
    if ctx.invoked_subcommand is not None:
        return
    app = ToadApp()
    app.run()


@main.command("acp")
@click.argument("command", metavar="COMMAND")
def acp(command: str):
    app = ToadApp(acp_command=command)
    app.run()


if __name__ == "__main__":
    main()
