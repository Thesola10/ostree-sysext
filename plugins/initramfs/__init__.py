import gi

gi.require_version("OSTree", "1.0")

from gi.repository            import OSTree
from ostree_sysext.extensions import Extension, CompatVote


def check_compatible(root: OSTree.Deployment, exts: list[Extension]) \
        -> tuple[CompatVote, str]:
    '''The initramfs generator does not have a say in compatibility.
    '''
    return CompatVote.APPROVE, ""

def deploy_finish(root: OSTree.Deployment, exts: list[Extension]) \
        -> tuple[CompatVote, str]:
    '''Generate initramfs from the complete stack of extensions'''
    pass
