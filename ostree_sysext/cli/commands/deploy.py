import os

from rich.console   import Console
from logging        import debug, error, warn
from pathlib        import Path
from gi.repository  import OSTree, Gio

from ..common       import find_sysext_by_ids
from ...extensions  import DeployState, Extension
from ...systemd     import refresh_sysexts
from ...deployment  import DeploymentSet
from ...repo        import open_system_repo
from ...environment import MutableExtension, get_current_deployment


def _deploy(console: Console, **args):
    ds = get_current_deployment()
    if ds is None:
        repo = open_system_repo(Path('ostree'))
        sr = OSTree.Sysroot()
        sr.load()
        ds = DeploymentSet(repo, root=sr.get_booted_deployment(), exts=[])

    for ex in find_sysext_by_ids(args['sysext']):
        if ex.get_state() == DeployState.EXTERNAL:
            warn(f"Extension '{ex.get_id()}' is not managed by OSTree-sysext.")
            continue
        if ex.get_state() == DeployState.ACTIVE:
            warn(f"Extension '{ex.get_id()}' is already active.")
            continue
        if type(ex) is MutableExtension:
            ex.deploy()
        else:
            ds.exts.append(ex)

    ds.commit()
    ds.apply()
    refresh_sysexts('--mutable=auto') # TODO: track auto vs imported

def _undeploy(console: Console, **args):
    ds = get_current_deployment()

    for ex in find_sysext_by_ids(args['sysext']):
        if ex.get_state() == DeployState.EXTERNAL:
            warn(f"Extension '{ex.get_id()}' is not managed by OSTree-sysext.")
            continue
        if ex.get_state() == DeployState.INACTIVE:
            warn(f"Extension '{ex.get_id()}' is already inactive.")
            continue
        if type(ex) is MutableExtension:
            ex.undeploy()
        else:
            ds.exts.remove(ex)

    ds.commit()
    ds.apply()
    refresh_sysexts('--mutable=auto')
