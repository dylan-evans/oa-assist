
import inspect

from pydantic import BaseModel
from typing import Callable


class ToolboxError(Exception):
    """
    Represents an error in tool loading.
    """


class ToolboxFunction(BaseModel):
    name: str
    description: str
    signature: inspect.Signature
    callback: Callable[[], None] | None = None

    @classmethod
    def from_function(cls, func):
        sig = inspect.signature(func)
        return cls(
            name = func.__name__,
            description = inspect.getdoc(func),
            signature = sig,
            callback = func,
        )

    def __call__(self, other, *args, **kwargs):
        print(self, other, args, kwargs)
        if self.callback is not None:
            callback(other, *args, **kwargs)


def toolbox(cls):
    tfns = []
    for name, member in inspect.getmembers(cls, lambda m: getattr(m, "tool_function", False)):
        desc = inspect.getdoc(member)
        if desc:
            tfns.append(ToolboxFunction(name=name, description=inspect.getdoc(member)))
        else:
            raise ToolboxError("A docstring is required for toolbox function as it provides the LLM with instructions")
    return cls


def tool_function(meth):
    meth.tool_function = True
    return meth


toolbox.function = tool_function


@toolbox
class TestToolbox1:
    @toolbox.function
    def fun1(self):
        """Tool function description."""
        print("fun1")

    @toolbox.function
    def fun2(self):
        print("fun2")


t1 = TestToolbox1()
t1.fun1()
