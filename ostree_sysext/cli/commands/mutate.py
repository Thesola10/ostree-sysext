import os

from rich.console   import Console
from logging        import debug, error, warn


from ..common       import find_sysext_by_ids
from ...extensions  import DeployState, Extension
from ...systemd     import refresh_sysexts


def _cmd(console: Console, **args):
    warn("mutate not implemented")
    pass
