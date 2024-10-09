import gi

gi.require_version('OSTree', '1.0')

from gi.repository  import OSTree, Gio
from pathlib        import Path

def open_system_repo(path: str) -> OSTree.Repo:
    '''Returns the OSTree Repo object for the given repository, setting up
    deployment areas for sysext if not already done
    '''
    repo = OSTree.Repo.new(Gio.File.new_for_path(Path(path).joinpath('repo')))
    repo.open()
    return repo


