from enum       import Enum
from pathlib    import Path

class DeployState(Enum):
    '''List of possible deployment states for a given Extension.
    '''
    EXTERNAL = 0  # Not managed by ostree-sysext (e.g. /var/lib/extensions)
    ACTIVE   = 1  # Applied by systemd-sysext
    INACTIVE = 2  # Removed from systemd-sysext paths
    IMPORTED = 3  # For mutables, applied but read-only
    STAGED   = 4  # Detectable by systemd-sysext but not applied
    UNSTAGED = 5  # Applied but removed from systemd-sysext dirs
    INCOMPAT = 6  # os-release ID mismatch
    OUTDATED = 7  # Version check mismatch

class UpdateState(Enum):
    AVAIL   = 0 # An update exists and can be applied without issues
    WARN    = 1 # Update has issues, can be bypassed using --force
    VETO    = 2 # Update process is impossible, cannot be bypassed
    UNAVAIL = 3 # No update exists
    UNKNOWN = 4 # An error occured while checking for updates

class CompatVote(Enum):
    APPROVE = 0 # No objections
    WARN    = 1 # Objection can be bypassed using --force
    VETO    = 2 # Objection cannot be bypassed

class TransactionType(Enum):
    ADD     = 0 # Add one or more packages to an extension
    REMOVE  = 1 # Remove one or more packages from an extension
    UPDATE  = 2 # Build an updated version of the extension
    USER0   = 128   #
    USER1   = 129   # Implementation-specific transactions
    USER2   = 130   #
    USER3   = 131   #


class Extension:
    DEPLOY_PATH = Path('/','run','extensions')

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

    def get_root(self):
        raise NotImplemented()
