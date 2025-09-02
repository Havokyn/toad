# Toad notes

This is notes.md in the root of the repository.
I'm using this file to keep track of what works in Toad and what doesn't.

## What works

- Settings works (press `F2` or `ctrl+comma`)
- You can have a chat with the LLM.
- You can navigate the output with alt+up and alt+down. Hit `return` to bring up a context menu.
- The prompt is quite functional (see placeholder text for help)

## What doesn't quite work

- There is a directory tree to explore the project files (press `f3`). It doesn't do much yet.

## The prompt

A lot of work has gone in to the prompt recently.

Hopefully it is quite intuitive. You can probably use it without instruction.

Hit "!" to enter shell mode and enter a shell command. The output is shown inline with the conversation. A subset of ANSI sequences are supported, so commands with color will generally work. There is no way to cancel a command yet. Press escape, or backspace the first position to return to prompt mode. There is a approve-list of commands that automatically enable shell mode, this will be editable eventually.

Hit "/" to enter a slash command. Auto complete should work. Currently the only working shell command is /about.

Hit "@" to pick a file. This will open a fizzy finder dialog, enter a few characters to narrow down the search. Hit return to insert the path, or escape to exit.

## ToDo

- Implement the back-end protocol. Since starting Toad, the [Agent Client Protocol](https://agentclientprotocol.com/overview/introduction) appeared. This sounds a lot like what I had in mind, and I may use this rather than rolling my own.
- Separating a current working directory from a project directory.
- More ANSI support, possibly even supporting embedded apps.
- Moving long-running processes to a list view, for things like servers.