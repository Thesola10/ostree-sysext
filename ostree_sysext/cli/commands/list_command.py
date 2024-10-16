import os

from rich.console   import Console
from rich.table     import Table
from rich.text      import Text
from rich           import box
from logging        import debug, error, warn

from ...extensions  import DeployState, Extension
from ...environment import list_sysexts, list_mutables

table_states = {
    DeployState.ACTIVE:   Text("active",    style="green bold"),
    DeployState.INACTIVE: Text("inactive"),
    DeployState.IMPORTED: Text("imported",  style="green"),
    DeployState.EXTERNAL: Text("external",  style="bright_white"),
    DeployState.STAGED:   Text("staged",    style="yellow bold"),
    DeployState.UNSTAGED: Text("unstaged",  style="yellow"),
    DeployState.INCOMPAT: Text("incompat",  style="red"),
    DeployState.OUTDATED: Text("outdated",  style="red bold")
}

class DummyExtension(Extension):
    state: DeployState
    id: str
    name: str
    version: str

    def __init__(self, id, name, version, state):
        self.id = id
        self.name = name
        self.version = version
        self.state = state

    def get_state(self):
        return self.state

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

def print_extension(tb: Table, ext: Extension):
    tb.add_row(ext.get_id(), ext.get_name(), ext.get_version(), table_states[ext.get_state()])

def _cmd(console: Console, **args):
    tb = Table(box=box.SIMPLE)
    tb.add_column("ID", justify="right", no_wrap=True)
    tb.add_column("NAME")
    tb.add_column("VERSION", no_wrap=True)
    tb.add_column("STATE")

    for ext in list_sysexts():
        print_extension(tb, ext)

    mutables = list_mutables()
    if len(mutables) > 0:
        tb.add_row()
        for mut in mutables:
            print_extension(tb, mut)

    tb.add_row()

#    print_extension(tb, DummyExtension("initramfs", "Locally built initramfs", "2ac7148d", DeployState.ACTIVE))
    console.print(tb)
