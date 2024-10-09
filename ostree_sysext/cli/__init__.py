import click
import os
import sys
import logging
import functools

from click_option_group import OptionGroup
from rich.console       import Console
from rich.logging       import RichHandler

from .. import __version__

cons = Console()
common_group = OptionGroup("Common options for ostree-sysext")

def _use_common_group(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

# For some reason, OSTree sends our own subcommand name when calling,
# drop it before entering click logic.
def main_fixed_for_ostree():
    if sys.argv[1] == 'sysext':
        sys.argv = sys.argv[1:]
        sys.argv[0] = 'ostree sysext'
    return main()

@click.group(invoke_without_command=True,
             help='test')
@_use_common_group
@click.option('--sysroot', default='/',
              help='Use system root')
@click.version_option(__version__)
@click.pass_context
def main(ctx: click.Context, **kwargs):
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
