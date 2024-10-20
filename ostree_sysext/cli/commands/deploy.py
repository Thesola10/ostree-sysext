import os

from rich.console   import Console
from logging        import debug, error, warn

from ..common       import find_sysext_by_ids
from ...extensions  import DeployState, Extension
from ...systemd     import refresh_sysexts


def _deploy(console: Console, **args):
    for ex in find_sysext_by_ids(args['sysext']):
        if ex.get_state() == DeployState.EXTERNAL:
            warn(f"Extension '{ex.get_id()}' is not managed by OSTree-sysext.")
            continue
        if ex.get_state() == DeployState.ACTIVE:
            warn(f"Extension '{ex.get_id()}' is already active.")
            continue
        ex.deploy()
    refresh_sysexts('--mutable=auto')

def _undeploy(console: Console, **args):
    for ex in find_sysext_by_ids(args['sysext']):
        if ex.get_state() == DeployState.EXTERNAL:
            warn(f"Extension '{ex.get_id()}' is not managed by OSTree-sysext.")
            continue
        if ex.get_state() == DeployState.INACTIVE:
            warn(f"Extension '{ex.get_id()}' is already inactive.")
            continue
        ex.undeploy()
    refresh_sysexts('--mutable=auto')
