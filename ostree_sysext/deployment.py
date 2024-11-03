import os

from gi.repository  import Gio, OSTree
from logging        import warn, error
from pathlib        import Path

from .repo          import RepoExtension, open_system_repo, ref_is_deployment_set, NOFLAGS
from .extensions    import Extension, DeployState
from .plugin        import survey_compatible, survey_deploy_finish


class DeploymentSet:
    exts: list[RepoExtension]
    repo: OSTree.Repo
    root: OSTree.Deployment
    ref: str
    mtree: OSTree.MutableTree

    # Hash of properties to invalidate ref
    digest: int

    def __init__(self, repo: OSTree.Repo, ref: str = None,
                 root: OSTree.Deployment = None,
                 exts: list[RepoExtension] = None):
        '''Construct a DeploymentSet.
        If ref is set, the relevant OSTree commit is opened and this object
        is constructed from its contents.

        If a root and exts are set, the object is constructed without a commit.
        '''
        self.repo = repo

        if ref is None:
            self.root = root
            self.exts = exts

        elif root is None and exts is None:
            self.ref = ref
            self.exts = []
            commit = repo.read_commit(ref)
            assert ref_is_deployment_set(commit)

            staged = commit.out_root.get_child('staged')
            staged_files = list(staged.enumerate_children("standard::*", NOFLAGS))
            for sfile in staged_files:
                target = sfile.get_attribute_as_string("standard::symlink-target")
                self.exts.append(RepoExtension(repo, target[-66:-2]))

            sysroot = OSTree.Sysroot()
            sysroot.load()
            self.root = sysroot.get_booted_deployment()

            self.digest = hash(tuple(self.exts))
        else:
            raise ValueError("ref cannot be specified alongside root and exts")

    def _is_committed(self) -> bool:
        if self.ref is None:
            return False
        if hash(tuple(self.exts)) != self.digest:
            return False
        return True

    def commit(self, force = False) -> str:
        '''Write and pin an OSTree commit for the given deployment state
        '''
        # 1. Invoke compatibility survey
        survey_compatible(root, exts, force)
        # 2. Invoke deploy finish survey
        # 3. Commit result to OSTree
        pass

    def apply(self, force = False):
        '''Apply and replace the current deployment set with this one.
        Will also update /run/extensions.
        '''
        # 1. Invoke compatibility survey
        survey_compatible(root, exts, force)
        # 2. Link checkout to /run/ostree/extensions (and to deploy/xxx.0.extensions)
        # 3. Replace extension set in /run/extensions with /run/ostree/extensions/staged
        pass

    def get_extensions(self) -> list[RepoExtension]:
        return self.exts

    def get_root(self) -> OSTree.Deployment:
        return self.root
