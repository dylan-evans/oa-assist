import rich
import rich.box
from ._dep.rich import Console, Table, Column
import click
from pydantic import BaseModel

from .assistant import Assistant
from .cli import cli, CLI, ShortcutGroup
from .tool_functions import DEFAULT_FUNCTIONS


def show_assistant(console: Console, assistant: Assistant):
    console.print(f"Name = {assistant.name}, ID = {assistant.id}")


@cli.group(invoke_without_command=True)
@click.pass_context
def assistant(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_assistants)


@assistant.command(name="list")
@click.pass_obj
def list_assistants(obj: CLI):
    table = Table(
        ":question_mark:",
        "Name",
        "ID",
        "Model",
        Column("Instructions", no_wrap=True),
        title="Assistants",
        box=rich.box.SIMPLE_HEAD
    )
    with obj.console.status("Working..."):
        for item in obj.openai.beta.assistants.list():
            selected = obj.config.selected.assistant_id == item.id

            table.add_row(
                ":star:" if selected else "",
                item.name,
                item.id,
                item.model,
                item.instructions.split("\n")[0].strip(),
                style="bold green" if selected else "",
            )
    obj.console.print(table)


@assistant.command
@click.pass_obj
@click.argument("assistant_id", nargs=-1)
def delete(obj: CLI, assistant_id):
    with obj.console.status("Working..."):
        for id in assistant_id:
            obj.console.print(f"Deleting assistant [bold]{id}[/bold].")
            obj.openai.beta.assistants.delete(assistant_id=id)


@assistant.command
@click.pass_obj
@click.argument("assistant_id")
@click.option("--name", "-n", is_flag=True)
def select(obj: CLI, assistant_id: str, name: bool):
    with obj.console.status("Working..."):
        if name:
            for assist in obj.openai.beta.assistants.list():
                if assist.name == assistant_id:
                    break
            else:
                raise ValueError(f"Unknown name: '{assistant_id}'")
        else:
            assist = obj.openai.beta.assistants.retrieve(assistant_id)
        obj.config.selected.assistant_id = assist.id
        obj.config.save()
        obj.console.print(f"[bold]{assist.id}[/bold] is now selected.")


@assistant.command
@click.pass_obj
@click.argument("model")
@click.argument("name")
@click.argument("instructions")
@click.option("--retrieval/--no-retrieval", default=False)
@click.option("--code-interpreter/--no-code-interpreter", default=True)
@click.option("--select", "-s", is_flag=True)
def create(obj: CLI, model, name, instructions, retrieval, code_interpreter, select):
    with obj.console.status("Working..."):
        assist = obj.openai.beta.assistants.create(
            model=model,
            name=name,
            instructions=instructions,
            tools=[{"type": "code_interpreter"}] + [{"type": "function", "function": func.get_function()} for func in DEFAULT_FUNCTIONS],
        )
    obj.console.print("Created: ")
    show_assistant(obj.console, assist)
    if select:
        obj.config.selected.assistant_id = assist.id
        obj.config.save()
        obj.console.print(f"[bold]{assist.id}[/bold] is now selected.")


@assistant.command
@click.pass_obj
@click.argument("model")
@click.argument("name")
@click.argument("instructions")
@click.option("--retrieval/--no-retrieval", default=False)
@click.option("--code-interpreter/--no-code-interpreter", default=True)
@click.option("--select", "-s", is_flag=True)
def update():
    pass
