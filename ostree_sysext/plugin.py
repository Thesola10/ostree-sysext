# will manage loading plugins when a component requests it.
import sys
import pkgutil
import importlib

from logging                import warn, error
from gi.repository          import OSTree

from .extensions            import Extension, CompatVote

def survey_compatible(root: OSTree.Deployment, exts: list[Extension], force=False) \
        -> tuple[CompatVote, str]:
    '''Veto for sysext compatibility.
    Given a deployment root, and a set of enabled extensions, determine if the
    merged state does not give rise to conflicts.
    '''
    assert os.getpid() == 1, "Deployment code invoked outside sandbox"
    for plugin in _import_plugins('/usr/lib/ostree-sysext/plugins'):
        res, msg = plugin.check_compatible(root, exts)
        if res == CompatVote.WARN and force:
            warn(f"{plugin.__name__}: {msg}")
        elif res != CompatVote.APPROVE:
            return res, f"{plugin.__name__}: {msg}"
    return CompatVote.APPROVE, ""

def survey_deploy_finish(root: OSTree.Deployment, exts: list[Extension]) \
        -> tuple[CompatVote, str]:
    '''Commands to run to generate stateful files.
    You will be chroot'ed to the target sysroot, with all extensions merged.
    The naked sysroot will be available in /run/baseroot (DO NOT LINK TO IT).
    The work directory for the stateful commit will be in /run/ostree/extensions
    and will be committed after all hooks finish.
    '''
    for plugin in _import_plugins('/usr/lib/ostree-sysext/plugins'):
        res, msg = plugin.deploy_finish(root, exts)
        if res == CompatVote.WARN and force:
            warn(f"{plugin.__name__}: {msg}")
        elif res != CompatVote.APPROVE:
            return res, f"{plugin.__name__}: msg"
    return CompatVote.APPROVE, ""


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
