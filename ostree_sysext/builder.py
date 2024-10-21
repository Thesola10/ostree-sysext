import sys
import pkgutil
import importlib

from enum                   import Enum
from logging                import warn, error
from gi.repository          import OSTree

from .extensions            import Extension, CompatVote, UpdateState, TransactionType


def check_update(builder: str, root: OSTree.Deployment, ext: Extension,
                 force=False) -> tuple[UpdateState, str]:
    '''Check for locally-built extension updates.
    Given a deployment root, and an extension, determine if updates are
    available and feasible for the given extension.
    '''
    pass

def perform_transaction(builder: str, root: OSTree.Deployment, ext: Extension,
                        what: TransactionType, targets: list[str],
                        options: dict,
                        force=False) -> tuple[CompatVote, str]:
    '''Run a transiaction in an extension.
    Given a deployment root, an extension, and a transaction with targets and
    options, perform the changes needed to create a new commit.
    '''
    pass

def list_builders(plugpath: str):
    oldpath = sys.path.copy()

    sys.path.insert(0, plugpath)
    for mod in pkgutil.iter_modules([plugpath]):
        importlib.import_module(mod.name)
        realmod = sys.modules[mod.name]
        if "check_update" and "perform_transaction" in dir(realmod):
            yield realmod
        else:
            warn(f"Builder '{name}' is not a valid ostree-sysext builder.")
    sys.path = oldpath
    return
