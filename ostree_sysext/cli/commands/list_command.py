import os

from rich.console   import Console
from rich.table     import Table
from rich.text      import Text
from rich           import box
from logging        import debug, error, warn

STATE_ACTIVE = Text("active", style="green bold")
STATE_INACTIVE = Text("inactive")
STATE_IMPORTED = Text("imported", style="green")
STATE_EXTERNAL = Text("external", style="bright_white")
STATE_STAGED = Text("staged", style="yellow bold")
STATE_UNSTAGED = Text("unstaged", style="yellow")

def _cmd(console: Console, **args):
    warn("the following output is a proof of concept")
    tb = Table(box=box.SIMPLE)
    tb.add_column("ID", justify="right", no_wrap=True)
    tb.add_column("NAME")
    tb.add_column("VERSION", no_wrap=True)
    tb.add_column("STATE")

    tb.add_row("sdk", "Fedora 41 Developer Tools", "41.0.1284", STATE_ACTIVE)
    tb.add_row("my-extension", "extension demo for Fedora", "1", STATE_EXTERNAL)
    tb.add_row("hello", "Hello!", "1.0", STATE_STAGED)
    tb.add_row("goodbye", "See ya later", "0.1", STATE_UNSTAGED)
    tb.add_row()
    tb.add_row("mutable:usr", "Mutable /usr directory", "", STATE_INACTIVE)
    tb.add_row("mutable:etc", "Mutable /etc directory", "", STATE_IMPORTED)
    tb.add_row()
    tb.add_row("initramfs", "Locally built initramfs", "2ac7148d", STATE_ACTIVE)
    console.print(tb)
