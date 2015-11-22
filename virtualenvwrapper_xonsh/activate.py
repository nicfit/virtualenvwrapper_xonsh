# -*- coding: utf-8 -*-
import builtins
from pathlib import Path
from argparse import ArgumentParser
from builtins import __xonsh_env__ as env

from .env import (env_dir, project_dir, env_root_dir, ensureEnv, getAllEnvs,
                  selectEnv)


ACTIVATE_XONSH = """#!/usr/bin/env xonsh
import builtins
from pathlib import Path
from builtins import __xonsh_env__ as env

env_d = Path('{env_d}')
predeactivate_script = Path('{predeactivate}')
postdeactivate_script = Path('{postdeactivate}')

$VIRTUAL_ENV = str(env_d)

$PATH.insert(0, str(env_d / 'bin'))

if "PYTHONHOME" in env:
    $_OLD_VIRTUAL_PYTHONHOME = $PYTHONHOME
    del env["PYTHONHOME"]

def _deactivate(args, stdin=None):
    builtins.aliases['source']([str(predeactivate_script)])

    $PATH.remove(str(env_d / "bin"))
    if "_OLD_VIRTUAL_PYTHONHOME" in env:
        $PYTHONHOME = $_OLD_VIRTUAL_PYTHONHOME

    builtins.aliases['source']([str(postdeactivate_script)])

    del builtins.aliases['deactivate']
    del env["VIRTUAL_ENV"]

builtins.aliases['deactivate'] = _deactivate
"""

PREACTIVATE_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import project_dir, env_dir
print("preactivate")
"""

POSTACTIVATE_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import project_dir, env_dir
print("postactivate")
"""

PREDEACTIVATE_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import project_dir, env_dir
print("predeactivate")
"""

POSTDEACTIVATE_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import project_dir, env_dir
print("postdeactivate")
"""

GET_ENV_DETAILS_XONSH = """#!/usr/bin/env xonsh
print("gen_env_details")
"""


# {script_prefix: (script_basename: script_template)
_hook_scripts = {s: ("{}.xonsh".format(s), "{}_XONSH".format(s.upper()))
                   for s in ["preactivate", "activate", "postactivate",
                             "predeactivate", "postdeactivate",
                             "get_env_details"]}


def _concreteHookPath(hook, hook_d):
    return Path(hook_d) / "bin" / Path(_hook_scripts[hook][0])


def runHookScript(script, env_d=None):
    if not env_d:
        if not env_dir():
            raise RuntimeError("No VIRTUAL_ENV active")
        env_d = Path(env_dir())
    else:
        env_d = Path(env_d)

    hook_path = env_d / "bin" / Path(_hook_scripts[script][0])
    hook_script = _concreteHookPath(script, env_d)
    if hook_script.exists():
        builtins.aliases['source']([str(hook_script)])


def activate(env_d):
    subst = {"env_d": str(env_d),
             "predeactivate": str(_concreteHookPath("predeactivate", env_d)),
             "postdeactivate": str(_concreteHookPath("postdeactivate", env_d)),
            }
    for hook in _hook_scripts:
        script = _concreteHookPath(hook, env_d)
        templ = _hook_scripts[hook][1]
        # Install templates if not already existing
        if not script.exists():
            with script.open("w") as file:
                file.write(globals()[templ].format(**subst))

    env["VIRTUAL_ENV"] = str(env_d)
    builtins.project_dir = project_dir
    builtins.env_dir = env_dir

    runHookScript("preactivate")
    runHookScript("activate")
    runHookScript("postactivate")


@ensureEnv
def cdproject(args=None, stdin=None):
    project_file = Path(env_dir()) / ".project"
    if project_file.exists():
        # cd to project dir
        with project_file.open() as fp:
            project_dir = fp.read().strip()
            builtins.aliases["cd"]([project_dir])


@ensureEnv
def cdvirtualenv(args, stdin=None):
    builtins.aliases["cd"]([env_dir()])


@ensureEnv
def cdsitepackages(args, stdin=None):
    env_d = Path(env_dir()) / "lib"
    pkgs_dir = [f for f in env_d.glob("python*")][0] / 'site-packages'
    builtins.aliases["cd"]([str(pkgs_dir)])


def lsvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="lsvirtualenv")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-b", action="store_false", dest="longmode",
                       help="Brief mode.", default=True)
    group.add_argument("-l", action="store_true", dest="longmode",
                       help="Long mode.", default=True)
    args = parser.parse_args(args)

    all_envs = getAllEnvs()
    for venv in all_envs:
        print(venv)
        if args.longmode:
            print("{}".format("=" * len(venv)))
            runHookScript("get_env_details", Path(env_root_dir()) / venv)
            print()


def cpvirtualenv(args, stdin=None):
    # TODO
    print("cpvirtualenv")
def mkvirtualenv(args, stdin=None):
    # TODO
    print("mkvirtualenv")


def rmvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="rmvirtualenv")
    parser.add_argument("env_names", nargs='+',
                        help="The virtualenvs to remove.")

    args = parser.parse_args(args)
    import ipdb; ipdb.set_trace()
    env_d = Path(selectEnv(args.env_name))
    runHookScript("get_env_details", env_d)
    # TODO
    print("rmvirtualenv")
    # selectEnv
    # Don't delete active
    # pre hooks
    # cd out of env
    # rm
    # posts hooks


def showvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="showvirtualenv")
    parser.add_argument("env_name", nargs='?', default=None,
                        help="If not specified the currently active env is "
                             "used.")

    args = parser.parse_args(args)
    env_d = Path(selectEnv(args.env_name))
    runHookScript("get_env_details", env_d)


@ensureEnv
def editvirtualenv(args, stdin=None):
    # TODO
    env_d = Path(env_dir())
    print("TODO", env_d)


_helpers = {
        "cdproject": cdproject,
        "cdvirtualenv": cdvirtualenv,
        "cdsitepackages": cdsitepackages,
        "lsvirtualenv": lsvirtualenv,
        "showvirtualenv": showvirtualenv,
        "rmvirtualenv": rmvirtualenv,
        #"cpvirtualenv": cpvirtualenv,
        #"mkvirtualenv": mkvirtualenv,
        #"editvirtualenv": editvirtualenv,
        }

for name, func in _helpers.items():
    builtins.aliases[name] = func
