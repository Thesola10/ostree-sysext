import os
import pwd

from ctypes         import CDLL, POINTER, Structure, c_char_p, c_int, c_uint32, c_ulong, c_size_t, get_errno
from ctypes.util    import find_library
from typing         import Callable
from pathlib        import Path
from logging        import error
from tempfile       import mkdtemp
from functools      import reduce
from sys            import exit


libc = CDLL(find_library('c'), use_errno=True)
libc.mount.argtypes = (c_char_p, c_char_p, c_char_p, c_ulong, c_char_p)
libc.umount.argtypes = (c_char_p,)

MS_REMOUNT = 32
MS_BIND = 4096


class CFSOpts(Structure):
    _fields_ = [('objdirs', POINTER(c_char_p)),
                ('n_objdirs', c_size_t),
                ('workdir', c_char_p),
                ('upperdir', c_char_p),
                ('expected_fsverity_digest', c_char_p),
                ('flags', c_uint32),
                ('idmap_fd', c_int),
                ('image_mountdir', c_char_p),
                ('reserved', c_uint32 * 4),
                ('reserved2', c_char_p * 4)]

def mount(what, where, fs, opts):
    if libc.mount(what.encode(), where.encode(), fs.encode(), 0, opts.encode()):
        error(f"mount({where}): {os.strerror(get_errno())}")
        raise OSError(get_errno())

def umount(what):
    if libc.umount(str(what).encode()):
        error(f"umount({what}): {os.strerror(get_errno())}")
        raise OSError(get_errno())

def mount_composefs(img, where, opts: CFSOpts):
    libcfs = CDLL(find_library('composefs'), use_errno=True)
    libcfs.lcfs_mount_image.argtypes = (c_char_p, c_char_p, CFSOpts)
    if libcfs.lcfs_mount_image(img.encode(), where.encode(), opts):
        error(f"lcfs_mount_image({where}): {errno.errorcode[get_errno()]}")


def edit_sysroot(fn: Callable):
    '''Run a process in the bare root with read/write access.
    Useful for working on an OSTree deployment root.
    '''
    child = os.fork()
    if child > 0:
        return os.waitpid(child, 0)
    else:
        os.unshare(os.CLONE_NEWNS|os.CLONE_NEWPID)
        if os.getcwd() != '/':
            os.chroot(os.getcwd())
        if libc.mount(b"", str(Path('/','sysroot')).encode(), b"", MS_REMOUNT|MS_BIND, b""):
            error(f"mount(/sysroot): {errno.errorcode[get_errno()]}")
            exit(1)
        exit(fn())
    pass

def edit_sandbox(fn: Callable, layers: list[Path], upper: Path, work: Path):
    '''Run a process in the given layered set sandbox.
    Useful for building or editing a sysext.
    '''
    child = os.fork()
    if child > 0:
        return os.waitpid(child, 0)
    else:
        myuser = os.getuid()
        if myuser == 0:
            boxuser = pwd.getpwnam("ostree-sysext")
            os.setuid(boxuser)
            myuser = boxuser
        os.unshare(os.CLONE_NEWUSER)

        with open("/proc/self/setgroups", "w") as sg:
            sg.write("deny")

        umap = open("/proc/self/uid_map", "w")
        gmap = open("/proc/self/gid_map", "w")

        umap.write(f"0 {myuser} 1")
        gmap.write(f"0 {myuser} 1")

        umap.close()
        gmap.close()

        os.unshare(os.CLONE_NEWNS|os.CLONE_NEWPID)

        tgt = mkdtemp(prefix="ostree-sysext-")
        lower = reduce(lambda l, r: f"{str(l)}:{str(r)}", layers)
        mount("ostree-sysext", tgt, "overlay",
              f"lowerdir={lower},upperdir={str(upper)},workdir={str(work)},userxattr")
        os.chroot(tgt)

        # we need to be a child of our NEWPID ns to mount /proc
        mt = os.fork()
        if mt > 0:
            os.waitpid(mt, 0)
        else:
            mount("proc", "/proc", "proc", "")
        exit(fn())

    pass
