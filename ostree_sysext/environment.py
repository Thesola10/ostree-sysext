import os
import pwd

from logging        import error
from mntfinder      import getMountPoint, getAllMountPoints
from pathlib        import Path


from .systemd       import ExternalExtension, list_deployed, list_staged, refresh_sysexts
from .repo          import RepoExtension, open_system_repo, find_sysext_refs
from .extensions    import Extension, DeployState
from .deployment    import DeploymentSet


class MutableExtension(Extension):
    MUTABLE_BACKING_PATH = Path('var','lib','ostree-sysext','mutable')
    MUTABLE_DEPLOY_PATH = Path('var','lib','extensions.mutable')

    root: str
    id: str

    def __init__(self, root: str):
        self.root = root
        self.id = f"mutable:{root}"

    def get_name(self):
        return f"Mutable /{self.root} directory"

    def get_version(self):
        return ""

    def get_state(self):
        mi = getMountPoint(Path('/', self.root))
        if not self.MUTABLE_BACKING_PATH.joinpath(self.root).exists():
            return DeployState.EXTERNAL
        if mi is None:
            return DeployState.INACTIVE
        if 'rw' in mi.options:
            return DeployState.ACTIVE

        lower = list(filter(lambda o: o.startswith('lowerdir='), mi.options))[0]
        lowerdirs = lower[len('lowerdir='):].split(':')
        if str(Path('/', self.MUTABLE_DEPLOY_PATH, self.root)) in lowerdirs:
            return DeployState.IMPORTED
        return DeployState.INACTIVE

    def get_rel_info(self):
        raise ValueError("Mutables do not have a release-info")

    def deploy(self):
        if self.get_state() == DeployState.EXTERNAL:
            raise ValueError("Cannot deploy an external mutable!")
        if not self.MUTABLE_DEPLOY_PATH.exists():
            self.MUTABLE_DEPLOY_PATH.mkdir()
        os.symlink(Path('..','ostree-sysext','mutable',self.root),
                   self.MUTABLE_DEPLOY_PATH.joinpath(self.root))

    def undeploy(self):
        if self.get_state() == DeployState.EXTERNAL:
            raise ValueError("Cannot undeploy an external mutable!")
        self.MUTABLE_DEPLOY_PATH.joinpath(self.root).unlink()


def list_sysexts() -> list[Extension]:
    '''Return a list of Extension objects discovered at the current root.
    PWD needs to be the root we are operating in.
    '''
    repo = open_system_repo(Path('ostree'))
    exts = [RepoExtension(repo, ref) for ref in find_sysext_refs(repo)]
    repo_ids = [ex.get_id() for ex in exts]
    staged_ids = list_staged()
    deployed_ids = list_deployed()

    # is this even worth tracking?
    for id, dir in staged_ids.items():
        if id not in repo_ids:
            exts.append(ExternalExtension(id, dir))

    for id in deployed_ids:
        if (id in staged_ids.keys()) or (id in repo_ids):
            continue
        exts.append(ExternalExtension(id, '/'))
    return exts

def list_mutables() -> list[MutableExtension]:
    '''Return a list of MutableExtension objects discovered at the current root.
    PWD needs to be the root we are operating in.
    '''
    mutables = MutableExtension.MUTABLE_DEPLOY_PATH
    backing = MutableExtension.MUTABLE_BACKING_PATH
    exts = []
    if mutables.exists():
        for mut in mutables.iterdir():
            if not mut.name.startswith('.'):
                exts.append(MutableExtension(mut.name))
    if backing.exists():
        for mut in backing.iterdir():
            if mut.name not in [x.root for x in exts] and not mut.name.startswith('.'):
                exts.append(MutableExtension(mut.name))
    return exts

def get_current_deployment() -> DeploymentSet:
    '''Return the DeploymentSet for the active commit found under /run/ostree/extensions
    '''
    deployset = Path('run','ostree','extensions')
    if not deployset.exists():
        return None
    if not deployset.is_symlink():
        raise ValueError("/run/ostree/extensions must be a symbolic link")

    commit = deployset.readlink().name[:-2]
    return DeploymentSet(open_system_repo(Path('ostree')), commit)

