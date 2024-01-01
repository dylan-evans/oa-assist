import os
from pathlib import Path
from typing import ClassVar, Any
from contextlib import contextmanager

import blinker
import pydantic
from ._dep.openai import Thread

USER_CONFIG = Path("~/.config/oa-assist/config.json").expanduser()


def load_user_config(path: Path = USER_CONFIG) -> "UserConfig":
    try:
        return UserConfig.model_validate_json(path.read_text())
    except IOError:
        return UserConfig()


def save_user_config(config: "UserConfig", path: Path = USER_CONFIG):
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json())


class Labels(pydantic.BaseModel):
    assistant: dict[str, str] = {}
    thread: dict[str, str] = {}
    run: dict[str, str] = {}


class Cache(pydantic.BaseModel):
    thread: dict[str, Thread] = {}


class SelectionIdentifiers(pydantic.BaseModel, validate_assignment=True):
    changed_signal: ClassVar[blinker.Signal] = blinker.signal("changed")

    assistant_id: str | None = None
    thread_id: str | None = None
    run_id: str | None = None

    @pydantic.model_validator(mode="after")
    @classmethod
    def _trigger_selected_field_updated(cls, data: Any):
        cls.changed_signal.send("updated")
        return data

class UserConfig(pydantic.BaseModel):
    selected: SelectionIdentifiers = SelectionIdentifiers()
    labels: Labels = Labels()
    cache: Cache = Cache()

    def save(self):
        save_user_config(self)

    @contextmanager
    def update(self):
        yield self
        self.save()
