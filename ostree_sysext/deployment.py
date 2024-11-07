import os

from gi.repository  import Gio, OSTree
from logging        import warn, error
from pathlib        import Path
from tempfile       import mkdtemp

from .repo          import RepoExtension, open_system_repo, ref_is_deployment_set, commit_dir, pin_ref, deploy_aware, NOFLAGS
from .extensions    import Extension, DeployState
from .plugin        import survey_compatible, survey_deploy_finish
from .sandbox       import umount, edit_sysroot


class DeploymentSet:
    DEPLOY_PATH = Path('/','run','ostree','extensions')

    exts: list[RepoExtension]
    repo: OSTree.Repo
    root: OSTree.Deployment
    ref: str

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
            self.ref = None

        elif root is None and exts is None:
            self.exts = []
            commit = repo.read_commit(ref)
            assert ref_is_deployment_set(commit)

            self.ref = commit.out_commit

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
        if self._is_committed():
            return self.ref

        tgt = mkdtemp(prefix="ostree-sysext-")
        survey_compatible(self.root, self.exts, force)

        Path(tgt, 'staged').mkdir()
        for ext in self.exts:
            Path(tgt, 'staged', ext.get_id()).symlink_to(f"/{ext.get_root()}")

        Path(tgt, 'state').mkdir()
        survey_deploy_finish(self.root, self.exts, tgt, force)

        err, ref = edit_sysroot(lambda: (0, commit_dir(self.repo, tgt, parent=self.ref)))
        if err:
            raise OSError(err)
        self.ref = ref
        self.digest = hash(tuple(self.exts))

        self.repo = OSTree.Repo.new(self.repo.get_path())
        self.repo.open()
        # TODO: flip-flop ref pin @ ostree-sysext/osname/<deploy>/<ext>
        return self.ref

    def apply(self, force = False):
        '''Apply and replace the current deployment set with this one.
        Will also update /run/extensions.
        '''
        survey_compatible(self.root, self.exts, force)

        dep_space = Path('ostree', 'deploy', self.root.get_osname(), 'extensions', 'deploy')
        deploy_aware(self.repo, self.ref, dep_space, self.DEPLOY_PATH)

        for ent in Extension.DEPLOY_PATH.iterdir():
            if ent.is_mount():
                umount(str(ent))
                ent.rmdir()
            elif ent.is_symlink():
                ent.unlink()
            else:
                raise ValueError(f"Found {str(ent)}, which is neither a mount nor a symlink.")
        for ext in self.exts:
            dep_ext = ext.EXTENSION_PATH.joinpath(ext.get_id(), 'deploy')
            deploy_aware(self.repo, ext.commit, dep_ext, ext.DEPLOY_PATH.joinpath(ext.get_id()))

        sr = OSTree.Sysroot()
        sr.load()
        dep = sr.get_deployment_dirpath(self.root)
        os.symlink(f'../extensions/deploy/{self.ref}.0', f'{dep}.extensions')

    def get_extensions(self) -> list[RepoExtension]:
        return self.exts

    def get_root(self) -> OSTree.Deployment:
        return self.root
