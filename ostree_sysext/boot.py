import os

from pathlib                import Path
from gi.repository          import OSTree, Gio

from .deployment            import DeploymentSet
from .repo                  import open_system_repo

def get_deployment() -> DeploymentSet:
    dep_path = ""
    repo = open_system_repo('/sysroot/ostree')
    with open('/proc/cmdline', 'r') as cmdf:
        cmdl = cmdf.read().split(' ')
        osys = list(filter(lambda s: s.startswith("ostree-sysext="), cmdl))
        if len(osys) == 1:
            dep_path = Path(osys[0].removeprefix("ostree-sysext="))
    if dep_path == "":
        sr = OSTree.Sysroot()
        sr.load()
        dep = sr.get_booted_deployment()
        dx_path = Path('/', f"{sr.get_deployment_dirpath(dep)}.extensions")
        dep_path = Path(dx_path.parent, dx_path.readlink())

    return DeploymentSet(repo, dep_path.name[:-2])



def boot_main():
    dep = get_deployment()
    dep.apply(syslink=False)
