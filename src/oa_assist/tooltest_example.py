import json
import subprocess

from tooltest import Toolbox, toolbox


sample = Toolbox("sample")

@sample.function
def _function(arg1: int, arg2: str, arg3: str | None = None) -> str:
    """
    Returns arg1 as a string if non-zero, arg3 if it is not None or arg2 by default.
    """
    return str(arg1) or arg3 or arg2


#print(json.dumps(list(sample.schema())))


@toolbox
class Alternate:
    def __init__(self, name):
        print("Alternate.__init__")

    @toolbox.function
    def pub_method(self, arg1: str, arg2: int = 0):
        """
        A method.
        """
        return arg1 or str(arg2)

    def any_other(self, foo):
        pass


#alt = Alternate("Alternate")

#print(json.dumps(list(alt.schema())))


@toolbox
class Shell:
    @toolbox.function
    def run_shell_command(self, command: str, input: str | None = None):
        """Execute a single shell command using: bash -c '{command}'"""
        proc = subprocess.run(self.command, shell=True, input=self.input, capture_output=True)
        return proc.stdout + proc.stderr


sh = Shell()
#print(json.dumps(list(sh.schema())))
