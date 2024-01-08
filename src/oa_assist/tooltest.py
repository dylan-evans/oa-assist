import json
import inspect
import functools
import importlib.util
from pathlib import Path

import wrapt
from pydantic import BaseModel, create_model


class ToolboxError(Exception):
    pass

class ToolboxLoader:
    def __init__(self):
        pass

    def load_from_file(self, path: Path):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name, member in inspect.getmembers(mod):
            val = getattr(mod, name)
            assert val == member
            print(name, member, "->", val)
            if isinstance(val, (Toolbox, ToolboxProxy)):
                print(name, "------------------------------", member)
        assert mod.sh == getattr(mod, "sh")
        print("sh", mod.sh, type(mod.sh), isinstance(mod.sh, ToolboxProxy), mod.sh.__class__.__bases__)
        print(dir(mod))



class Toolbox:
    def __init__(self, name=None):
        self.name = name
        print("Toolbox.__init__", name)
        self._functions = {}

    def schema(self):
        print("funcs", self._functions)
        for func in self._functions.values():
            yield func_to_json_schema(func)

    @wrapt.decorator
    def function(self, wrapped, instance, *args, **kwargs):
        """
        A decorator adding functions to the toolbox.
        """

        self._functions[wrapped.__name__] = wrapped
        return wrapped(*args, **kwargs)


class ToolboxProxy(wrapt.ObjectProxy, Toolbox):
    def __init__(self, wrapped, name=None):
        super(ToolboxProxy, self).__init__(wrapped)
        self.name = name
        Toolbox.__init__(self)
        for member_name, member in inspect.getmembers(wrapped, lambda m: hasattr(m, "__toolbox_function__")):
            self._functions[member_name] = member

    def __call__(self, *args, **kwargs):
        self.__wrapped__(*args, **kwargs)


class ToolboxFunctionProxy(wrapt.ObjectProxy):
    def __init__(self, wrapped):
        print("**** Wrapping toolbox function", wrapped)
        super(ToolboxFunctionProxy, self).__init__(wrapped)

    def __call__(self, *args, **kwargs):
        self.__wrapped__(*args, **kwargs)

    def is_tb(self):
        print("Yes")
        return True


def toolbox_function(wrapped=None):
    if wrapped is None:
        return toolbox_function

    @wrapt.decorator
    def _tb_func(wrapped, instance, args, kwargs):
        print("toolbox_function")
        return wrapped(*args, **kwargs)

    wrapped.__toolbox_function__ = True

    return _tb_func(wrapped)


def toolbox(wrapped=None, name=None):
    if wrapped is None:
        return toolbox

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if not isinstance(wrapped, type):
            raise ToolboxError("The toolbox decorator is only intended to be used with classes")
        return ToolboxProxy(wrapped(*args, **kwargs))

    return wrapper(wrapped)

# Just a shortcut
toolbox.function = toolbox_function


def func_to_json_schema(func):
    """
    Convert a function to a schema the easy way using pydantic.
    """
    sig = inspect.signature(func)
    for n, p in sig.parameters.items():
        print(n, p.annotation)

    fields = {}
    for name, param in sig.parameters.items():
        if param.annotation == param.empty:
            raise ToolboxError(f"Type annotation is required (missing from '{name}')")
        fields[name] = (param.annotation, param.default if param.default != param.empty else ...)

    model = create_model(func.__name__, **fields)

    return {
        "name": func.__name__,
        "description": inspect.getdoc(func),
        "parameters": model.model_json_schema()
    }


if __name__ == '__main__':
    ToolboxLoader().load_from_file(Path("./tooltest_example.py"))