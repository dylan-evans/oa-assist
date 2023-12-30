import time

from ._dep import openai as oa
from ._dep.openai import Thread, ThreadMessage
from ._dep import rich as ui
from ._dep.rich import Console, ConsoleOptions, Panel, Markdown, Prompt, RenderResult


class MessageView:
    def __init__(self, message: ThreadMessage):
        self.message = message

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        if self.message.role == "assistant":
            yield from self.show_assistant_message()
        else:
            yield from self.show_user_message()

    def show_assistant_message(self):
        values = (con.text.value for con in self.message.content if con.type == "text")
        for text in values:
            panel = Panel(
                Markdown(text),
                title=f"Assistant {self.message.assistant_id or ''}",
                style="white on color(237)",
                expand=False,
            )
            yield panel

    def show_user_message(self):
        values = (con.text.value for con in self.message.content if con.type == "text")
        for text in values:
            yield f"[bold red]User:[/] {text}"


class MessageListView:
    def __init__(self, thread: list[ThreadMessage], reverse=True):
        self.thread = thread
        if reverse:
            self.thread.reverse()

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        for mesg in self.thread:
            yield MessageView(mesg)


class InteractiveChat:
    def __init__(self, initial_message: str):
        pass

    def send_cmd(console, thread, line):
        op = thread.send(line)
        with console.status("Working...", spinner="bouncingBall") as status:
            while not op.ready():
                for mesg in op.get_log_messages():
                    console.log(mesg)
                time.sleep(0.2)
            resp = op.get_response()

        console.print(MessageView(resp))
