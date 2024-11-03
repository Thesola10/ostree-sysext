# will manage loading plugins when a component requests it.
import os
import sys
import pkgutil
import importlib

from logging                import warn, error
from gi.repository          import OSTree
from typing                 import Callable
from pathlib                import Path

from .extensions            import Extension, CompatVote
from .sandbox               import edit_sandbox

def survey_compatible(root: OSTree.Deployment, exts: list[Extension], force=False) \
        -> tuple[CompatVote, str]:
    '''Veto for sysext compatibility.
    Given a deployment root, and a set of enabled extensions, determine if the
    merged state does not give rise to conflicts.
    '''
    for plugin in _import_plugins('/usr/lib/ostree-sysext/plugins'):
        res, msg = _call_sandbox(plugin.check_compatible, root, exts)
        if res == CompatVote.WARN and force:
            warn(f"{plugin.__name__}: {msg}")
        elif res != CompatVote.APPROVE:
            return res, f"{plugin.__name__}: {msg}"
    return CompatVote.APPROVE, ""

def survey_deploy_finish(root: OSTree.Deployment, exts: list[Extension], tgt: Path, force=False) \
        -> tuple[CompatVote, str]:
    '''Commands to run to generate stateful files.
    You will be chroot'ed to the target sysroot, with all extensions merged.
    The work directory for the stateful commit will be in /run/ostree/extensions
    and will be committed after all hooks finish.
    '''
    for plugin in _import_plugins('/usr/lib/ostree-sysext/plugins'):
        binds = { tgt: Path('/','run','ostree','extensions') }
        res, msg = _call_sandbox(plugin.deploy_finish, root, exts, binds)
        if res == CompatVote.WARN and force:
            warn(f"{plugin.__name__}: {msg}")
        elif res != CompatVote.APPROVE:
            return res, f"{plugin.__name__}: msg"
    return CompatVote.APPROVE, ""


def _call_sandbox(fn: Callable, root: OSTree.Deployment, exts: list[Extension], \
                  binds: dict[Path, Path] = None):
    sr = OSTree.Sysroot()
    sr.open()
    layers = [sr.get_deployment_dirpath(root)]
    for ext in exts:
        layers.append(ext.get_root())
    return edit_sandbox(lambda: fn(root, exts), layers, binds=binds)

def _import_plugins(plugpath: str):
    oldpath = sys.path.copy()

    sys.path.insert(0, plugpath)
    for mod in pkgutil.iter_modules([plugpath]):
        importlib.import_module(mod.name)
        if "check_compatible" and "deploy_finish" in dir(sys.modules[mod.name]):
            yield sys.modules[mod.name]
        else:
            warn(f"Plugin '{name}' is not a valid ostree-sysext plugin.")

    sys.path = oldpath
    return
