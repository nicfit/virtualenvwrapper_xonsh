# -*- coding: utf-8 -*-
import builtins

from argparse import ArgumentParser
from pathlib import Path
from builtins import __xonsh_env__ as env

from .env import env_root_dir, getAllEnvs
from .activate import activate, cdproject, lsvirtualenv


def workon(args, stdin=None):
    desc = "Deactivate any currently activated virtualenv and activate the "\
           "named environment, triggering any hooks in the process."

    env_d = Path(env_root_dir())

    parser = ArgumentParser('workon', description=desc)
    parser.add_argument("env_name", nargs='?', default=None,
                        help="If not specified a list of available "
                             "environments is printed.")
    args = parser.parse_args(args)

    if not args.env_name:
        lsvirtualenv(['-b'])
        return

    if "deactivate" in builtins.aliases:
        # alias is removed by the function
        builtins.aliases['deactivate']([])

    # Activate the env
    env_d = env_d / Path(args.env_name)
    activate(env_d)
    cdproject()

