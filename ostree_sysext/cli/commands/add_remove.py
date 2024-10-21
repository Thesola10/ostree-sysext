import os

from rich.console   import Console
from logging        import debug, error, warn


from ..common       import find_sysext_by_ids
from ...extensions  import DeployState, Extension
from ...systemd     import refresh_sysexts


def _add(console: Console, **args):
    # pull remote refs, get their id and pin them to ostree/extension/<id>/0
    # can also be used to create local editable sysext i guess
    warn("not implemented add")
    pass

def _remove(console: Console, **args):
    # scan for use and drop refs, garbage-collect
    warn("not implemented remove")
    for ext in find_sysext_by_ids(args['sysext']):
        pass
