import click
import os
import sys
import logging
import functools

from click_option_group import OptionGroup
from rich.console       import Console
from rich.logging       import RichHandler

from ..                 import __version__
from .commands          import list_command, deploy, add_remove, mutate
from ..dbus             import dbus_main
from ..boot             import boot_main

cons = Console()
common_group = OptionGroup("Common options for ostree-sysext")

def _use_common_group(fn):
    @common_group.option('--sysroot', default='/', help='Use system root')
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

# For some reason, OSTree sends our own subcommand name when calling,
# drop it before entering click logic.
def main_fixed_for_ostree():
    if len(sys.argv) > 1 and sys.argv[1] == 'sysext':
        sys.argv = sys.argv[1:]
        sys.argv[0] = 'ostree sysext'
    return main()


@click.group(invoke_without_command=True,
             help='Handy system extension manager for OSTree systems')
@_use_common_group
@click.version_option(__version__)
@click.pass_context
def main(ctx: click.Context, **kwargs):
    global sysroot
    _debug = os.getenv('OSTREE_SYSEXT_DEBUG') is not None
    logging.basicConfig(
            level    = 'DEBUG' if _debug else 'INFO',
            format   = '%(message)s',
            handlers = [RichHandler(rich_tracebacks = True,
                                    tracebacks_suppress = [click],
                                    log_time_format     = "",
                                    console             = cons,
                                    show_path           = _debug)
                       ])
    if kwargs['sysroot'] != '':
        os.chdir(kwargs['sysroot'])
    else:
        os.chdir('/')
    if ctx.invoked_subcommand is None:
        list_command._cmd(cons, **kwargs)


@main.command("list", help='List installed system extensions')
@_use_common_group
def _list(**kwargs):
    list_command._cmd(cons, **kwargs)


@main.command('add', help='Import a system extension without deploying it')
@click.argument('ref', nargs=-1, required=True)
@_use_common_group
def _add(**kwargs):
    add_remove._add(cons, **kwargs)

@main.command("remove", help='Remove a system extension completely')
@click.argument('sysext', nargs=-1, required=True)
@_use_common_group
def _remove(**kwargs):
    add_remove._remove(cons, **kwargs)


@main.command("deploy", help='Deploy a system extension on top of this system')
@click.argument('sysext', nargs=-1, required=True)
@_use_common_group
def _deploy(**kwargs):
    deploy._deploy(cons, **kwargs)

@main.command("undeploy", help='Disable an active system extension')
@click.argument('sysext', nargs=-1, required=True)
@_use_common_group
def _undeploy(**kwargs):
    deploy._undeploy(cons, **kwargs)


@main.command("rollback", help='Revert a system extension to a previous version')
@_use_common_group
def _rollback(**kwargs):
    logging.warn("rollback")

@main.command("mutate", help='Make a system directory read/write')
@_use_common_group
def _mutate(**kwargs):
    mutate._cmd(cons, **kwargs)

@main.command("build", help='Build a system extension from a Containerfile')
@_use_common_group
def _build(**kwargs):
    logging.warn("build")

@main.command("edit", help='Modify and commit a local system extension')
@_use_common_group
def _edit(**kwargs):
    logging.warn("edit")


@main.command("upgrade", help='Update all system extensions')
@_use_common_group
def _upgrade(**kwargs):
    logging.warn("upgrade")

@main.command("live-update", help='Apply an update to the base system as an extension')
@_use_common_group
def _live_update(**kwargs):
    logging.warn("live-update")

@main.command("initramfs", help='Enable or disable local initramfs regeneration')
@_use_common_group
def _initramfs(**kwargs):
    logging.warn("initramfs")


@main.command("daemon", hidden=True,
              help='Internal command used to invoke daemon over D-Bus')
def _daemon(**kwargs):
    return dbus_main()

@main.command("early-boot", hidden=True,
              help='Internal command used to load sysexts on boot')
def _early_boot(**kwargs):
    return boot_main()
