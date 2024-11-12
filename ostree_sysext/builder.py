import sys
import pkgutil
import importlib

from enum                   import Enum
from logging                import warn, error
from gi.repository          import OSTree
from base64                 import b64encode
from random                 import randbytes

from .extensions            import Extension, CompatVote, UpdateState, TransactionType
from .sandbox               import edit_sandbox, edit_sysroot
from .repo                  import RepoExtension, commit_dir


def check_update(builder: str, root: OSTree.Deployment, ext: RepoExtension,
                 force=False) -> tuple[UpdateState, str]:
    '''Check for locally-built extension updates.
    Given a deployment root, and an extension, determine if updates are
    available and feasible for the given extension.
    '''
    mod = find_builder(Path('/usr/lib/ostree-sysext/builders'), builder)
    randid = b64encode(randbytes(9)).decode()
    up = Path('/', 'tmp', 'ostree-sysext-{randid}')
    res, msg = _call_sandbox(lambda: mod.check_update(root, ext, context), root, up)

    return res, f"{builder}: {msg}"

def build_extension(repo: OSTree.Repo, builder: str, root: OSTree.Deployment,
                    context: dict, force=False) -> tuple[CompatVote, str]:
    '''Build an extension from a build context.
    Given a deployment root and a build context, build and commit a system
    extension. The build context is a freeform dict.
    '''
    mod = find_builder(Path('/usr/lib/ostree-sysext/builders'), builder)
    randid = b64encode(randbytes(9)).decode()
    tgt = Path('/', 'var', 'tmp', 'ostree-sysext', f'build-{randid}')
    res, msg = _call_sandbox(lambda: mod.build_extension(root, context), root, tgt)
    if res == CompatVote.WARN and force:
        warn(f"{builder}: {msg}")
    elif res != CompatVote.APPROVE:
        return res, f"{builder}: {msg}"

    meta = { 'ostree-sysext.builder': builder, 'ostree-sysext.build-context': context }
    err, ref = edit_sysroot(lambda: (0, commit_dir(repo, tgt, meta=meta)))
    if err:
        raise OSError(err)
    return CompatVote.APPROVE, ref

def _call_sandbox(fn: Callable, root: OSTree.Deployment, \
                  upper: Path):
    sr = OSTree.Sysroot()
    sr.open()
    layers = [sr.get_deployment_dirpath(root)]
    binds = {Path('/', 'sysroot'): Path('/', 'sysroot')}

    work = upper.parent.joinpath(f'.work-{upper.name}')
    return edit_sandbox(fn, layers, upper=upper, work=work, binds=binds)

def find_builder(plugpath: str, name: str):
    oldpath = sys.path.copy()
    mymod = None

    sys.path.insert(0, plugpath)
    try:
        importlib.import_module(name)
        mymod = sys.modules[name]
        if not ("check_update" and "build_extension" in dir(mymod)):
            raise ValueError(f"Builder '{name}' is not a valid ostree-sysext builder.")
    finally:
        sys.path = oldpath
    return mymod

def list_builders(plugpath: str):
    oldpath = sys.path.copy()

    sys.path.insert(0, plugpath)
    for mod in pkgutil.iter_modules([plugpath]):
        importlib.import_module(mod.name)
        realmod = sys.modules[mod.name]
        if "check_update" and "build_extension" in dir(realmod):
            yield realmod
        else:
            warn(f"Builder '{name}' is not a valid ostree-sysext builder.")
    sys.path = oldpath
    return
