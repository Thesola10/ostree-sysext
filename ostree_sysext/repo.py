import gi

gi.require_version('OSTree', '1.0')

from gi.repository  import OSTree, Gio
from pathlib        import Path
from dotenv         import dotenv_values
from io             import StringIO

from .systemd       import list_staged, list_deployed
from .extensions    import Extension, DeployState

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
    if ext_rel.query_file_type(Gio.FileQueryInfoFlags.NONE) != Gio.FileType.DIRECTORY:
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

def find_sysext_refs(repo: OSTree.Repo, prefix = None):
    '''Inspect local refs for sysext metadata in their embedded tree.
    '''
    success, refs = repo.list_refs(prefix)
    for ref in refs.keys():
        if ref_is_sysext(repo.read_commit(ref)):
            yield ref


class RepoExtension(Extension):
    root: OSTree.RepoFile
    rel_info: dict
    id: str

    def __init__(self, repo: OSTree.Repo, ref: str):
        commit = repo.read_commit(ref)
        if not ref_is_sysext(commit):
            raise ValueError("Specified ref is not a valid OSTree sysext")
        self.root = commit.out_root
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

    def deploy(self):
        # Mount (composefs) or symlink into /run/extensions
        pass

    def undeploy(self):
        # Unmount/unlink from /run/extensions
        pass
