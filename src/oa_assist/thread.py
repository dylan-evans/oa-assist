
import click

from .cli import cli, CLI
from .ui import Working, Table

@cli.group
@click.pass_obj
def thread(obj: CLI):
    if obj.config.selected_assistant_id is None:
        raise click.ClickException("No assistant selected")


@thread.command
@click.option("--label", "-l")
@click.option("--select", "-s", is_flag=True)
@click.pass_obj
def create(obj: CLI, label: str, select: bool):
    with obj.console.status("Working..."):
        thread = obj.openai.beta.threads.create()
    if select:
        obj.config.selected_thread_id = thread.id
    if label:
        obj.config.labels.thread[thread.id] = label
    obj.config.cache.thread[thread.id] = thread
    obj.config.save()
    obj.console.print(f"Thread [bold]{thread.id}[/bold] created and selected.")


@thread.command
@click.pass_obj
def delete(obj: CLI):
    pass


@thread.command(name="list")
@click.pass_obj
def list_threads(obj: CLI):
    table = Table("", "Label", "ID", "Status", title="Threads", caption="Known threads only")
    for thread in obj.config.cache.thread.values():
        selected = obj.config.selected_thread_id == thread.id
        table.add_row(
            ":star:" if selected else "",
            obj.config.labels.thread.get(thread.id, ""),
            thread.id,
            "",
            style="bold green" if selected else "",
        )
    obj.console.print(table)
