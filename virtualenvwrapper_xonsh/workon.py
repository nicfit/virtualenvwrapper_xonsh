# -*- coding: utf-8 -*-
import builtins

from argparse import ArgumentParser
from pathlib import Path
from builtins import __xonsh_env__ as env

from .activate import activate, cdproject


def workon(args, stdin=None):

    desc = "Deactivate any currently activated virtualenv and activate the "\
           "named environment, triggering any hooks in the process."

    if "VIRTUALENVWRAPPER_HOOK_DIR" not in env:
        raise RuntimeError("virtualenvwrapper variable "
                           "$VIRTUALENVWRAPPER_HOOK_DIR not defined")
    env_dir = Path(env["VIRTUALENVWRAPPER_HOOK_DIR"])

    parser = ArgumentParser('workon', description=desc)
    parser.add_argument("env_name", nargs='?', default=None,
                        help="If not specified a list of available "
                             "environments is printed.")

    args = parser.parse_args(args)
    if not args.env_name:
        # Print all envs
        all_envs = []
        for f in env_dir.iterdir():
            if f.is_dir():
                all_envs.append(f.name)
        print("\n".join(sorted(all_envs)))
        return

    if "deactivate" in builtins.aliases:
        # alias is removed by the function
        builtins.aliases['deactivate']([])

    # Activate the env
    env_dir = env_dir / Path(args.env_name)
    activate(env_dir)
    cdproject()

