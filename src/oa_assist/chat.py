
from ._dep import openai as oa
from ._dep.openai import Thread, ThreadMessage
from ._dep import rich as ui
from ._dep.rich import Console, Panel, Markdown, Prompt, Columns



class ChatView:
    def __init__(self, console: Console):
        self.console = console

    def show_assistant_message(self, message: ThreadMessage):
        values = (con.text.value for con in message.content if con.type == "text")
        for text in values:
            panel = Panel(
                Markdown(text),
                title=f"Assistant {message.assistant_id or ''}",
                style="white on color(237)",
                expand=False,
            )
            self.console.print(panel)

    def show_user_message(self, message: ThreadMessage):
        values = (con.text.value for con in message.content if con.type == "text")
        for text in values:
            self.console.print(text)

    def show_thread(self, thread: Thread):
        pass

    def chat_prompt(self):
        while True:
            line = Prompt.get_input(
                self.console,
                "[bold red]chat:[/bold red] ",
                password=False
            ).strip()
            if not line:
                continue
            if line.startswith("\\"):  # Multiline mode
                pass
            if line.startswith("/"):  # Command mode
                pass


if __name__ == "__main__":
    console = Console()
    chat = ChatView(console)
    chat.show_assistant_message(ThreadMessage(
        id="123",
        assistant_id="assist1",
        content=[
            oa.MessageContentText(
                type="text",
                text=oa.Text(
                    value="Hello, world!",
                    annotations=[],
                ),
            ),
        ],
        created_at=0,
        file_ids=[],
        metadata=None,
        object="thread.message",
        role="assistant",
        run_id=None,
        thread_id="10"
    ))
