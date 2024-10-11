import os

from enum import Enum

def check_sysext() -> bool:
    '''Perform checks to verify that the system is ready to host systemd
    sysexts
    '''
    pass

def refresh_sysexts():
    os.system("systemd-sysext refresh")

class DeployState(Enum):
    EXTERNAL = 0  # Not managed by ostree-sysext (e.g. /var/lib/extensions)
    ACTIVE   = 1  # Applied by systemd-sysext
    INACTIVE = 2  # Removed from systemd-sysext paths
    IMPORTED = 3  # For mutables, applied but read-only
    STAGED   = 4  # Detectable by systemd-sysext but not applied
    UNSTAGED = 5  # Applied but removed from systemd-sysext dirs
    INCOMPAT = 6  # os-release ID mismatch
    OUTDATED = 7  # Version check mismatch

class Extension:
    DEPLOY_PATH = "/run/extensions"
    BOOT_PATH = "/.extra/sysext"
    CONFIG_PATH = "/etc/extensions"
    USER_PATH = "/var/lib/extensions"

    def get_state(self) -> DeployState:
        pass

    def get_id(self) -> str:
        pass

    def get_name(self) -> str:
        pass

    def get_version(self) -> str:
        pass

