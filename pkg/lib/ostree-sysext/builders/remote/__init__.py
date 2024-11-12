import gi

gi.require_version("OSTree", "1.0")

from gi.repository            import OSTree
from ostree_sysext.extensions import Extension, CompatVote


def check_update(root: OSTree.Deployment, ext: Extension, context: dict):
    '''Check that remote ref has new commits.
    '''
    pass

def build_extension(root: OSTree.Deployment, context: dict):
    '''This builder takes a single context key, 'remote_ref',
    and pulls from the given OSTree remote.
    '''
    pass
