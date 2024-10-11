from .systemd       import ExternalExtension, list_deployed, list_staged
from .repo          import RepoExtension, open_system_repo, find_sysext_refs
from .extensions    import Extension

def list_sysexts() -> list[Extension]:
    repo = open_system_repo('/ostree')
    exts = [RepoExtension(repo, ref) for ref in find_sysext_refs(repo)]
    repo_ids = [ex.get_id() for ex in exts]
    staged_ids = list_staged()
    deployed_ids = list_deployed()
    for id, dir in staged_ids.items():
        if id not in repo_ids:
            exts.append(ExternalExtension(id, dir))
    for id in deployed_ids:
        if (id in staged_ids.keys()) or (id in repo_ids):
            continue
        exts.append(ExternalExtension(id, '/'))
    return exts
