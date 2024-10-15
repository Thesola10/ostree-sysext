import os
import pwd

from pydbus     import SystemBus
from logging    import warn, error

build_user: int

def dbus_main():
    global build_user

    try:
        build_user = pwd.getpwnam("ostree-sysext")
    except:
        error("User 'ostree-sysext' does not exist.")
        exit(1)

    warn("hello")
