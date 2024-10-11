from enum       import Enum

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

    id: str
    rel_info: dict

    def get_id(self):
        return self.id

    def get_name(self):
        if "NAME" in self.rel_info:
            return self.rel_info["NAME"]
        else:
            return self.id

    def get_version(self):
        if "OSTREE_VERSION" in self.rel_info:
            return self.rel_info["OSTREE_VERSION"]
        else:
            return ""

    def get_rel_info(self):
        return self.rel_info

    def get_state(self):
        return DeployState.EXTERNAL

