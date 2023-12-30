import time
from logging import basicConfig, WARNING
from typing import List

import click
from click.core import Command, Context
import openai
import pydantic
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

from .chat import MessageListView, MessageView
from .assistant import AssistantInterface
from .config import UserConfig, load_user_config, save_user_config
from .tool_functions import DEFAULT_FUNCTIONS



class CLI(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    openai: openai.OpenAI
    console: Console
    config: UserConfig


class ShortcutGroup(click.Group):
    ALIASES = {
        "ls": "list",
        "rm": "delete",
    }

    def resolve_command(self, ctx: Context, args: List[str]) -> tuple[str | None, Command | None, List[str]]:
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args

    def get_command(self, ctx, cmd_name):
        return (
            super().get_command(ctx, cmd_name) or
            self.get_plural_command(ctx, cmd_name) or
            self.get_alias_command(ctx, cmd_name) or
            self.get_short_command(ctx, cmd_name)
        )

    def get_plural_command(self, ctx: Context, cmd_name: str):
        # TODO: doesn't work
        if cmd_name[-1] == 's':
            cmd = super().get_command(ctx, cmd_name[:-1])
            return cmd

    def get_alias_command(self, ctx: Context, cmd_name: str):
        if cmd_name in self.ALIASES:
            return self.get_command(ctx, self.ALIASES[cmd_name])

    def get_short_command(self, ctx, cmd_name: str):
        commands = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]

        if not commands:
            ctx.fail("Command not found")
        elif len(commands) > 1:
            ctx.fail("Ambiguous command '{cmd_name}")
        return super().get_command(ctx, commands[0])


@click.group(cls=ShortcutGroup)
@click.pass_context
def cli(ctx):
    basicConfig(level=WARNING)
    ctx.obj = CLI(
        openai=openai.OpenAI(),
        console=Console(),
        config=load_user_config(),
    )


# Ensure shortcuts are enabled for sub-groups.
cli.group_class = ShortcutGroup


@cli.command
@click.option("--message", "-m")
@click.pass_obj
def chat(obj: CLI, message: str | None):
    if obj.config.selected.assistant_id is None:
        raise click.ClickException("No assistant selected")

    acc = AssistantInterface.retrieve(obj.openai, obj.config.selected.assistant_id, DEFAULT_FUNCTIONS)

    console = Console()

    if obj.config.selected.thread_id:
        #thread_id = openai.beta.threads.retrieve(obj.config.selected.thread_id)
        thread = acc.retrieve_thread(obj.config.selected.thread_id)
        messages = openai.beta.threads.messages.list(obj.config.selected.thread_id)
        console.print(MessageListView(thread=list(messages)))
    else:
        thread = acc.create_thread()
        with obj.config.update() as conf:
            conf.selected.thread_id = thread.thread.id
            conf.cache.thread[thread.thread.id] = thread.thread
        #thread_id = openai.beta.threads.create()

    if message:
        console.print(f"[bold red]chat:[/bold red] {message}")
        send_cmd(console, thread, message)

    while True:
        line = Prompt.get_input(console, "[bold red]chat:[/bold red] ", password=False)
        if not line:
            continue
        send_cmd(console, thread, line)


def send_cmd(console, thread, line):
    op = thread.send(line)
    with console.status("Working...", spinner="bouncingBall") as status:
        while not op.ready():
            for mesg in op.get_log_messages():
                console.log(mesg)
            time.sleep(0.2)
        resp = op.get_response()

    console.print(MessageView(resp))
