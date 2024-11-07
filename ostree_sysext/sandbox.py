import os
import sys
import pwd

from ctypes         import CDLL, POINTER, Structure, c_char_p, c_int, c_uint32, c_ulong, c_size_t, get_errno
from ctypes.util    import find_library
from typing         import Callable
from pathlib        import Path
from logging        import error
from tempfile       import mkdtemp
from functools      import reduce


libc = CDLL(find_library('c'), use_errno=True)
libc.mount.argtypes = (c_char_p, c_char_p, c_char_p, c_ulong, c_char_p)
libc.umount.argtypes = (c_char_p,)

MS_RDONLY   = 1 << 0
MS_REMOUNT  = 1 << 5
MS_BIND     = 1 << 12

LCFS_MOUNT_FLAGS_REQUIRE_VERITY = 1 << 0
LCFS_MOUNT_FLAGS_READONLY       = 1 << 1
LCFS_MOUNT_FLAGS_IDMAP          = 1 << 3
LCFS_MOUNT_FLAGS_TRY_VERITY     = 1 << 4

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

def mount_composefs(img, where, verity: bytes = None, idmap: Path = None):
    libcfs = CDLL(find_library('composefs'), use_errno=True)
    libcfs.lcfs_mount_image.argtypes = (c_char_p, c_char_p, CFSOpts)

    flags = LCFS_MOUNT_FLAGS_REQUIRE_VERITY|LCFS_MOUNT_FLAGS_READONLY
    idmap_fd = -1
    if idmap is not None and idmap.exists():
        flags |= LCFS_MOUNT_FLAGS_IDMAP
        idmap_fd = os.open(str(idmap))
    repobjs = (c_char_p * 2)()
    repobjs[0] = b"/ostree/repo/objects"

    reserved = (c_uint32 * 4)()
    reserved2 = (c_char_p * 4)()
    opts = CFSOpts(repobjs, 1,
                   None, None, verity, flags,
                   idmap_fd, f"/tmp/{str(img)}".encode(), reserved, reserved2)

    if libcfs.lcfs_mount_image(str(img).encode(), str(where).encode(), opts):
        error(f"lcfs_mount_image({where}): {os.strerror(get_errno())}")
        raise OSError(get_errno())


def edit_sysroot(fn: Callable) -> tuple[int, str]:
    '''Run a process in the bare root with read/write access.
    Useful for working on an OSTree deployment root.
    Requires root privileges.
    '''
    r_fd, w_fd = os.pipe()
    child = os.fork()
    if child > 0:
        os.close(w_fd)
        pid, ret = os.waitpid(child, 0)
        return ret, os.read(r_fd, 1024).decode()
    else:
        os.unshare(os.CLONE_NEWNS|os.CLONE_NEWPID)
        if os.getcwd() != '/':
            os.chroot(os.getcwd())
        if libc.mount(b"", str(Path('/','sysroot')).encode(), b"", MS_REMOUNT|MS_BIND, b""):
            error(f"mount(/sysroot): {os.strerror(get_errno())}")
            exit(2)

        os.close(r_fd)
        ret, msg = fn()
        os.write(w_fd, msg.encode())
        sys.exit(ret)
    pass

def edit_sandbox(fn: Callable, layers: list[Path], \
                 upper: Path = None, work: Path = None, binds: dict[Path,Path] = None) \
        -> tuple[int, str]:
    '''Run a process in the given layered set sandbox.
    Useful for building or editing a sysext.
    Will discard root privileges.
    '''
    r_fd, w_fd = os.pipe()
    child = os.fork()
    if child > 0:
        os.close(w_fd)
        pid, ret = os.waitpid(child, 0)
        return ret, os.read(r_fd, 1024).decode()
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
        opt = ""
        if (upper is None) and (work is None):
            opt = f"lowerdir={lower},userxattr"
        else:
            opt = f"lowerdir={lower},upperdir={str(upper)},workdir={str(work)},userxattr"
        mount("ostree-sysext", tgt, "overlay", opt)
        mount("tmpfs", f"{tgt}/run", "tmpfs", "")
        mount("tmpfs", f"{tgt}/tmp", "tmpfs", "")

        if binds is not None:
            for k, v in binds.items():
                where = Path(tgt).joinpath(v.parts[1:])
                if not where.exists():
                    where.mkdir()
                if libc.mount(str(k).encode(), str(where).encode(), b"none", MS_BIND, b""):
                    error(f"mount({v}): {os.strerror(get_errno())}")
                    exit(2)
        os.chroot(tgt)

        # we need to be a child of our NEWPID ns to mount /proc
        mt = os.fork()
        if mt > 0:
            os.waitpid(mt, 0)
        else:
            mount("proc", "/proc", "proc", "")
        os.close(r_fd)
        ret, msg = fn()
        write(w_fd, msg)
        sys.exit(ret)

    pass
