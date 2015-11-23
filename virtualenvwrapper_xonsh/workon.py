# -*- coding: utf-8 -*-
import builtins

from argparse import ArgumentParser
from pathlib import Path
from builtins import __xonsh_env__ as env

from .env import envRootDir, useEnv
from .activate import activate, cdproject, lsvirtualenv, runHookScript


def workon(args, stdin=None):
    desc = "Deactivate any currently activated virtualenv and activate the "\
           "named environment, triggering any hooks in the process."

    env_d = envRootDir()

    parser = ArgumentParser('workon', description=desc)
    parser.add_argument("--reinstall", action="store_true",
                        help="Reinstall hook files.")
    parser.add_argument("env_name", nargs='?', default=None,
                        help="If not specified a list of available "
                             "environments is printed.")
    args = parser.parse_args(args)

    if not args.env_name:
        lsvirtualenv(['-b'])
        return

    if "deactivate" in builtins.aliases:
        # alias is removed by the function
        runHookScript("deactivate")

    env_d = useEnv(args.env_name)
    activate(env_d, reinstall=args.reinstall)
    cdproject(['-q'])
