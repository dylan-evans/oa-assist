import json
import re
import subprocess
from pathlib import Path
from typing import ClassVar, List
from abc import ABC
from logging import exception

import pydantic


class FunctionEventHandler(ABC):
    def log(self, mesg: str):
        pass

# TODO: rename BaseToolFunction
class BaseFunction(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    def __call__(self, events: FunctionEventHandler = FunctionEventHandler()):
        raise NotImplementedError()

    @classmethod
    def get_function(cls):
        return {
            "name": cls.NAME,
            "description": cls.DESCRIPTION,
            "parameters": ""
        }


class BaseToolBox(pydantic.BaseModel):
    name: str
    functions: list[BaseFunction]


class ExecFunction(BaseFunction):
    NAME: ClassVar[str] = "exec_shell"
    DESCRIPTION: ClassVar[str] = "Execute a single shell command using: bash -c '{command}'"
    command: str
    input: str | None = None

    def __call__(self, events: FunctionEventHandler = FunctionEventHandler()):
        events.log(f"Executing: {self.command}")
        proc = subprocess.run(self.command, shell=True, input=self.input, capture_output=True)
        return proc.stdout + proc.stderr


class WriteFileFunction(BaseFunction):
    NAME: ClassVar[str] = "write_file"
    DESCRIPTION: ClassVar[str] = "Write contenst to a file within a local directory"
    path: str
    content: str

    @pydantic.model_validator(mode="before")
    @classmethod
    def _validate(cls, data):
        path = re.sub(r"\.+", ".", data["path"])
        if path.startswith("/"):
            path = path[1:]
        data["path"] = path
        return data

    def __call__(self, events: FunctionEventHandler = FunctionEventHandler()):
        path = Path(self.path)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        events.log(f"Writing file: '{path}'")
        path.write_text(self.content)
        return '{"success": true}'


class ReadFileFunction(BaseFunction):
    NAME: ClassVar[str] = "read_file"
    DESCRIPTION: ClassVar[str] = """\
        Read content from a file within a local directory. If the path
        is a directory a list of files will be returned (sub-directories
        will have a trailing slash).
    """
    path: str

    @pydantic.model_validator(mode="before")
    @classmethod
    def _validate(cls, data):
        path = re.sub(r"\.+", ".", data["path"])
        if path.startswith("/"):
            path = path[1:]
        data["path"] = path
        return data

    def __call__(self, events: FunctionEventHandler = FunctionEventHandler()):
        path = Path(self.path)

        try:
            if path.is_dir():
                listing = [sub.name + ("/" if sub.is_dir() else "") for sub in path.iterdir()]
                events.log(f"Getting file list: '{path} -> {listing}")
                return json.dumps({
                    "success": True,
                    "path": str(path),
                    "file-type": "directory",
                    "content": listing,
                })

            events.log(f"Reading file: '{path}'")
            return json.dumps({
                "success": True,
                "path": str(path),
                "file-type": "file",
                "content": path.read_text()
            })
        except Exception:
            exception("Read failed")
            events.log(f"Read failed: '{path}'")
            return json.dumps({
                "success": False,
                "error": "Unable to access file"
            })


class GitCommandFunction(BaseFunction):
    NAME: ClassVar[str] = "git_command"
    DESCRIPTION: ClassVar[str] = "Execute a Git command within a repository."
    command: str
    args: List[str] = []
    repo_dir: str

    def __call__(self, events: FunctionEventHandler = FunctionEventHandler()):
        git_cmd = ["git", "-C", self.repo_dir] + [self.command] + self.args
        command_str = " ".join(git_cmd)
        events.log(f"Executing Git command: {command_str}")
        proc = subprocess.run(git_cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return {'success': True, 'output': proc.stdout}
        else:
            return {'success': False, 'error': proc.stderr}


DEFAULT_FUNCTIONS = [
    ReadFileFunction,
    WriteFileFunction,
    ExecFunction,
    GitCommandFunction,
]
