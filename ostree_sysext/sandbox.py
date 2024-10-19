import os
import pwd
import errno

from ctypes         import CDLL, c_char_p, c_ulong, get_errno
from ctypes.util    import find_library
from typing         import Callable
from pathlib        import Path


libc = CDLL(find_library('c'), use_errno=True)
libc.mount.argtypes = (c_char_p, c_char_p, c_char_p, c_ulong, c_char_p)
libc.umount.argtypes = (c_char_p,)

MS_REMOUNT = 32
MS_BIND = 4096


def mount(what, where, fs, opts):
    if libc.mount(what.encode(), where.encode(), fs.encode(), None, opts.encode()):
        error(f"mount({where}): {errno.errorcode[get_errno()]}")


def edit_sysroot(fn: Callable):
    '''Run a process in the bare root with read/write access.
    Useful for working on an OSTree deployment root.
    '''
    child = os.fork()
    if child > 0:
        return os.waitpid(child, 0)
    else:
        os.unshare(os.CLONE_NEWNS|os.CLONE_NEWPIDiiii)
        if os.getcwd() != '/':
            os.chroot(os.getcwd())
        if libc.mount(b"", str(Path('/','sysroot')).encode(), b"", MS_REMOUNT|MS_BIND, b""):
            error(f"mount(/sysroot): {errno.errorcode[get_errno()]}")
            exit(1)
        exit(fn())
    pass

def edit_sandbox(fn: Callable, layers: list[Path], upper: Path):
    '''Run a process in the given layered set sandbox.
    Useful for building or editing a sysext.
    '''
    boxuser = pwd.getpwnam("ostree-sysext")
    child = os.fork()
    if child > 0:
        return os.waitpid(child, 0)
    else:
        os.unshare(os.CLONE_NEWNS|os.CLONE_NEWPID)
        # then su as ostree-sysext and unshare(CLONE_NEWUSER)

    pass
