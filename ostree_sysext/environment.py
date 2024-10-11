from mntfinder      import getMountPoint
from pathlib        import Path

from .systemd       import ExternalExtension, list_deployed, list_staged
from .repo          import RepoExtension, open_system_repo, find_sysext_refs
from .extensions    import Extension, DeployState


class MutableExtension(Extension):
    dir: str
    id: str

    def __init__(self, dir: str):
        self.dir = dir
        self.id = f"mutable:{dir}"

    def get_name(self):
        return f"Mutable /{dir} directory"

    def get_version(self):
        return ""

    def get_state(self):
        mi = getMountPoint(Path('/').join(dir))
        if 'rw' in mi.options:
            return DeployState.ACTIVE
        lower = list(filter(lambda o: o.startswith('lowerdir='), mi.options))[0]
        lowerdirs = lower[len('lowerdir='):].split(':')
        if str(Path('/', 'var', 'lib', 'extensions.mutable', dir)) in lowerdirs:
            return DeployState.IMPORTED
        return DeployState.INACTIVE

    def get_rel_info(self):
        raise ValueError("Mutables do not have a release-info")

def list_sysexts() -> list[Extension]:
    repo = open_system_repo('/ostree')
    exts = [RepoExtension(repo, ref) for ref in find_sysext_refs(repo)]
    repo_ids = [ex.get_id() for ex in exts]
    staged_ids = list_staged()
    deployed_ids = list_deployed()
    for id, dir in staged_ids.items():
        if id not in repo_ids:
            exts.append(ExternalExtension(id, dir))
    for id in deployed_ids:
        if (id in staged_ids.keys()) or (id in repo_ids):
            continue
        exts.append(ExternalExtension(id, '/'))
    return exts

def list_mutables() -> list[MutableExtension]:
    mutables = Path('/', 'var', 'lib', 'extensions.mutable')
    exts = []
    if not mutables.exists():
        return exts
    for mut in mutables.iterdir():
        exts.append(MutableExtension(mut.name))
    return exts

