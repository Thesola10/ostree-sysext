import os

from rich.console   import Console
from logging        import debug, error, warn

from ...extensions  import DeployState, Extension
from ...environment import list_sysexts, list_mutables
from ...systemd     import refresh_sysexts


def _deploy(console: Console, **args):
    exts = list_sysexts() + list_mutables()
    match = []

    for exid in args['sysext']:
        match += [x for x in exts if x.get_id() == exid]
        if len(match) == 0:
            error(f"Extension '{exid}' not found.")
            exit(1)
    for ex in match:
        if ex.get_state() == DeployState.EXTERNAL:
            warn(f"Extension '{exid}' is not managed by OSTree-sysext.")
            continue
        if ex.get_state() == DeployState.ACTIVE:
            warn(f"Extension '{exid}' is already active.")
            continue
        ex.deploy()
    refresh_sysexts()

def _undeploy(console: Console, **args):
    exts = list_sysexts() + list_mutables()
    match = []

    for exid in args['sysext']:
        match += [x for x in exts if x.get_id() == exid]
        if len(match) == 0:
            error(f"Extension '{exid}' not found.")
            exit(1)
    for ex in match:
        if ex.get_state() == DeployState.EXTERNAL:
            warn(f"Extension '{exid}' is not managed by OSTree-sysext.")
            continue
        if ex.get_state() == DeployState.INACTIVE:
            warn(f"Extension '{exid}' is already inactive.")
            continue
        ex.undeploy()
    refresh_sysexts()
