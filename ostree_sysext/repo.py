import os
import gi

gi.require_version('OSTree', '1.0')

from gi.repository  import OSTree, Gio
from pathlib        import Path
from dotenv         import dotenv_values
from io             import StringIO
from logging        import warn

from .systemd       import list_staged, list_deployed
from .extensions    import Extension, DeployState
from .sandbox       import mount, umount, edit_sysroot, mount_composefs

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
        try:
            if ref_is_sysext(repo.read_commit(ref)):
                yield ref
        except:
            warn(f"Could not open ref \"{ref}\" for analysis")
            pass    # rpm-ostree sometimes keeps broken refs that can trip
                    # up the detector due to missing metadata

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
    rfd = os.open(repo.get_path().get_path(), os.O_RDONLY)
    repo.checkout_at(opts, rfd, str(destpath), commit)
    if composefs_is_enabled(repo):
        wr = OSTree.Repo.new(repo.get_path())
        wr.open()
        wr.checkout_composefs(None, rfd, str(destpath.joinpath('.ostree.cfs')), commit)
    return ""

def deploy_aware(repo: OSTree.Repo, ref: str, prefix: Path, dest: Path):
    '''Perform checkout checks, and deploy ref to target directory while
    applying composefs if present.
    '''
    local, _r, commit = repo.read_commit(ref)
    coutpath = Path(prefix, f'{commit}.0')
    if not coutpath.exists():
        edit_sysroot(lambda: (0, checkout_aware(repo, ref, prefix)))
    if coutpath.joinpath('.ostree.cfs').exists():
        dest.mkdir(parents=True, exist_ok=True)
        mount_composefs(coutpath.joinpath('.ostree.cfs'), dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(str(coutpath), str(dest))


def commit_dir(repo: OSTree.Repo, dir: Path, parent: str = None, \
        subject: str = None, body: str = None, meta: dict = None) -> str:
    '''Copy and commit a given directory into an OSTree ref
    '''
    wr = OSTree.Repo.new(repo.get_path())
    wr.open()
    wr.prepare_transaction()
    mtree = OSTree.MutableTree()
    wr.write_directory_to_mtree(Gio.File.new_for_path(str(dir)), mtree)
    done, mr = wr.write_mtree(mtree)
    done, ref = wr.write_commit(parent, subject, body, meta, mr)
    wr.commit_transaction()
    return ref

def pin_ref(repo: OSTree.Repo, commit: str, ref: str):
    '''Take a commit hash and pin it to a branch
    '''
    ret, val = edit_sysroot(repo.set_ref_immediate(None, ref, commit))
    if ret == 0:
        return val
    else:
        raise OSError(ret)


class RepoExtension(Extension):
    EXTENSION_PATH = Path('ostree','extensions')

    repo: OSTree.Repo
    commit: str
    root: OSTree.RepoFile
    rel_info: dict
    id: str
    builder: str
    build_context: dict

    def __init__(self, repo: OSTree.Repo, ref: str):
        commit = repo.read_commit(ref)
        if not ref_is_sysext(commit):
            raise ValueError("Specified ref is not a valid OSTree sysext")
        self.root = commit.out_root
        self.repo = repo
        self.commit = commit.out_commit

        res, meta = repo.read_commit_detached_metadata(self.commit)
        if meta is not None and 'ostree-sysext.builder' in meta.keys():
            self.builder = meta['ostree-sysext.builder']
            self.build_context = meta['ostree-sysext.build-context']

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
        osrel = None
        if staged and deployed:
            return DeployState.ACTIVE
        elif staged:
            return DeployState.STAGED
        elif deployed:
            return DeployState.UNSTAGED

        with open('etc/os-release') as osrf:
            osrel = dotenv_values(stream=osrf)
        if rel_info['ID'] != osrel['ID'] and rel_info['ID'] != '_any':
            return DeployState.INCOMPAT
        elif 'ARCHITECTURE' in rel_info.keys() \
                and rel_info['ARCHITECTURE'] != '_any' \
                and rel_info['ARCHITECTURE'] != os.uname().machine:
            return DeployState.INCOMPAT
        elif 'VERSION_ID' in rel_info.keys() \
                and rel_info['VERSION_ID'] != osrel['VERSION_ID']:
            return DeployState.OUTDATED
        return DeployState.INACTIVE

    def get_rel_info(self):
        return self.rel_info

    def get_root(self) -> Path:
        mypath = self.EXTENSION_PATH.joinpath(self.id, 'deploy')
        if not mypath.joinpath(f'{self.commit}.0').exists():
            checkout_aware(self.repo, self.commit, mypath)
        return mypath.joinpath(f'{self.commit}.0')

