from logging        import debug, error, warn

from ..environment  import list_sysexts, list_mutables
from ..extensions   import DeployState, Extension

def find_sysext_by_ids(ids: list[str]) -> list[Extension]:
    exts = list_sysexts() + list_mutables()
    match = []

    for exid in ids:
        match += [x for x in exts if x.get_id() == exid]
        if len(match) == 0:
            error(f"Extension '{exid}' not found.")
            exit(1)
    return match
