import os

from rich.console   import Console
from rich.table     import Table
from rich.text      import Text
from rich           import box
from logging        import debug, error, warn

from ...extensions  import DeployState, Extension
from ...environment import list_sysexts

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
#
#dummy_exts = [
#    DummyExtension("sdk", "Fedora 41 Developer Tools", "41.0.1284", DeployState.ACTIVE),
#    DummyExtension("thing", "Fedora 40 Something", "40.1.3018", DeployState.OUTDATED),
#    DummyExtension("my-extension", "extension demo for Fedora", "1", DeployState.EXTERNAL),
#    DummyExtension("hello", "Hello!", "1.0", DeployState.STAGED),
#    DummyExtension("goodbye", "See ya later", "0.1", DeployState.UNSTAGED),
#    DummyExtension("lol", "Debian Thingamajig", "9.0.1", DeployState.INCOMPAT),
#]

def print_extension(tb: Table, ext: Extension):
    tb.add_row(ext.get_id(), ext.get_name(), ext.get_version(), table_states[ext.get_state()])

def _cmd(console: Console, **args):
    warn("the following output is a proof of concept")
    tb = Table(box=box.SIMPLE)
    tb.add_column("ID", justify="right", no_wrap=True)
    tb.add_column("NAME")
    tb.add_column("VERSION", no_wrap=True)
    tb.add_column("STATE")

    for ext in list_sysexts():
        print_extension(tb, ext)

    tb.add_row()

    print_extension(tb, DummyExtension("mutable:usr", "Mutable /usr directory", "", DeployState.INACTIVE))
    print_extension(tb, DummyExtension("mutable:etc", "Mutable /etc directory", "", DeployState.IMPORTED))

    tb.add_row()

    print_extension(tb, DummyExtension("initramfs", "Locally built initramfs", "2ac7148d", DeployState.ACTIVE))
    console.print(tb)
