import os
import gi

gi.require_version('OSTree', '1.0')

from gi.repository  import OSTree, Gio
from pathlib        import Path
from dotenv         import dotenv_values
from io             import StringIO

from .systemd       import list_staged, list_deployed
from .extensions    import Extension, DeployState
from .sandbox       import mount, umount, edit_sysroot


NOFLAGS = Gio.FileQueryInfoFlags.NONE

def open_system_repo(path: str) -> OSTree.Repo:
    '''Returns the OSTree Repo object for the given repository, setting up
    deployment areas for sysext if not already done
    '''
    repo = OSTree.Repo.new(Gio.File.new_for_path(str(Path(path).joinpath('repo'))))
    repo.open()
    return repo

def ref_is_sysext(commit) -> bool:
    '''Predicate for valid filesystem info, given a response object from
    OSTree.Repo.read_commit()
    '''
    usr_lib = commit.out_root.get_child('usr').get_child('lib')
    ext_rel = usr_lib.get_child('extension-release.d')
    if ext_rel.query_file_type(NOFLAGS) != Gio.FileType.DIRECTORY:
        return False    # extension-release.d is missing or not a directory.

    rel_files = list(ext_rel.enumerate_children("standard::*", NOFLAGS))
    if len(rel_files) != 1:
        return False    # A sysext must contain exactly one extension-release.

    rel_name = rel_files[0].get_name()
    if not rel_name.startswith("extension-release."):
        return False    # The extension-release file must be named correctly.

    rel_file = ext_rel.get_child(rel_name)
    if rel_file.query_file_type(NOFLAGS) != Gio.FileType.REGULAR:
        return False    # extension-release must be a regular file.

    return True

def ref_is_deployment_set(commit) -> bool:
    '''Predicate for valid deployset info, given a response object from
    OSTree.Repo.read_commit()
    '''
    staged = commit.out_root.get_child('staged')
    state = commit.out_root.get_child('state')
    if staged.query_file_type(NOFLAGS) != Gio.FileType.DIRECTORY:
        return False    # staged is missing or not a directory.

    if state.query_file_type(NOFLAGS) != Gio.FileType.DIRECTORY or Gio.FileType.UNKNOWN:
        return False    # state is not a directory.

    return True

def find_sysext_refs(repo: OSTree.Repo, prefix = None):
    '''Inspect local refs for sysext metadata in their embedded tree.
    '''
    success, refs = repo.list_refs(prefix)
    for ref in refs.keys():
        if ref_is_sysext(repo.read_commit(ref)):
            yield ref

def composefs_is_enabled(repo: OSTree.Repo) -> bool:
    '''Check whether composefs is enabled in the OSTree repository.
    '''
    try:
        repo.get_config().get_keys('ex-integrity')
        cfs = repo.get_config().get_value('ex-integrity', 'composefs')
        return cfs == 'true'
    except:
        return False

def checkout_aware(repo: OSTree.Repo, ref: str, dest: str):
    '''Checkout ref into given space, while cleaning up previous deployments
    and generating composefs metadata if enabled.
    '''
    opts = OSTree.RepoCheckoutAtOptions()
    opts.enable_uncompressed_cache = True

    local, _r, commit = repo.read_commit(ref)
    destpath = Path(dest, f'{commit}.0')
    repo.checkout_at(opts, None, str(destpath), commit)
    if composefs_is_enabled():
        repo.checkout_composefs(None, None, str(destpath.joinpath('.ostree.cfs')), commit)

def commit_dir(repo: OSTree.Repo, dir: Path, parent: str = None, \
        subject: str = None, body: str = None, meta: dict = None) -> str:
    '''Copy and commit a given directory into an OSTree ref
    '''
    repo.prepare_transaction()
    mtree = OSTree.MutableTree()
    repo.write_directory_to_mtree(Gio.File.new_for_path(str(dir)), mtree)

    act = lambda: (0, repo.write_commit(parent, subject, body, meta, repo.write_mtree(mtree)))
    ret, val = edit_sysroot(act)
    if ret == 0:
        return val
    else:
        raise OSError(ret)

class RepoExtension(Extension):
    EXTENSION_PATH = Path('ostree','extensions')

    # TODO: Store builder as commit metadata for updating

    repo: OSTree.Repo
    commit: str
    root: OSTree.RepoFile
    rel_info: dict
    id: str

    def __init__(self, repo: OSTree.Repo, ref: str):
        commit = repo.read_commit(ref)
        if not ref_is_sysext(commit):
            raise ValueError("Specified ref is not a valid OSTree sysext")
        self.root = commit.out_root
        self.repo = repo
        self.commit = commit[2]
        ext_rel = commit.out_root \
                        .get_child('usr').get_child('lib') \
                        .get_child('extension-release.d')
        rel_name = list(ext_rel.enumerate_children("standard::*", NOFLAGS))[0].get_name()
        rel_file = ext_rel.get_child(rel_name)
        self.id = rel_name[len("extension-release."):]
        self.rel_info = dotenv_values(stream=StringIO(rel_file.load_contents().contents.decode()))

    def get_state(self):
        staged = self.id in list_staged().keys()
        deployed = self.id in list_deployed()
        if staged and deployed:
            return DeployState.ACTIVE
        elif staged:
            return DeployState.STAGED
        elif deployed:
            return DeployState.UNSTAGED
        else:
            return DeployState.INACTIVE

    def get_rel_info(self):
        return self.rel_info

    def get_root(self) -> Path:
        mypath = self.EXTENSION_PATH.joinpath(self.id, 'deploy')
        if not mypath.joinpath(f'{self.commit}.0').exists():
            checkout_aware(self.repo, self.commit, mypath)
        return mypath

    def deploy(self):
        # Mount (composefs) or symlink into /run/extensions
        # TODO: Retire in favor of deployment.DeploymentSet
        mypath = self.EXTENSION_PATH.joinpath(self.id, 'deploy')
        if not mypath.joinpath(f'{self.commit}.0').exists():
            checkout_aware(self.repo, self.commit, mypath)
        if composefs_is_enabled(self.repo):
            self.DEPLOY_PATH.joinpath(self.id).mkdir()
            mount(str(Path('/', mypath, f'{self.commit}.0', '.ostree.cfs')),
                  str(self.DEPLOY_PATH.joinpath(self.id)),
                  'composefs',
                  f'basedir={self.repo.get_path().get_path()}/objects')
        else:
            os.symlink(Path('/', mypath, f'{self.commit}.0'),
                       self.DEPLOY_PATH.joinpath(self.id))

    def undeploy(self):
        # Unmount/unlink from /run/extensions
        if self.DEPLOY_PATH.joinpath(self.id).is_mount():
            umount(self.DEPLOY_PATH.joinpath(self.id))
            self.DEPLOY_PATH.joinpath(self.id).rmdir()
        else:
            self.DEPLOY_PATH.joinpath(self.id).unlink()
