import os
import subprocess
import json

from pathlib        import Path
from .extensions    import Extension

SYSTEMD_SYSEXT_COMMAND = [ 'systemd-sysext', '--json=short' ]

def call_systemd(*args):
    '''Interact with the systemd-sysext command using JSON response
    given a set of arguments
    '''
    r = subprocess.run(SYSTEMD_SYSEXT_COMMAND + list(args), capture_output=True)
    return json.loads(r.stdout)

def check_sysext() -> bool:
    '''Perform checks to verify that the system is ready to host systemd
    sysexts
    '''
    pass

def list_deployed() -> list[str]:
    deployed = []
    for hier in call_systemd("status"):
        if hier['extensions'] != "none":
            deployed += hier['extensions']
    return list(set(deployed))

def list_staged() -> dict[str,str]:
    staged = {}
    for ext in call_systemd("list"):
        staged[ext['name']] = ext['path']
    return staged

def refresh_sysexts(*args):
    subprocess.run(SYSTEMD_SYSEXT_COMMAND + [ "refresh" ] + list(args))

