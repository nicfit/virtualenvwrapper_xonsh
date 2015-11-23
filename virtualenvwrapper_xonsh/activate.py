# -*- coding: utf-8 -*-
import sys
import shutil
import builtins
import subprocess
from pathlib import Path
from argparse import ArgumentParser
from builtins import __xonsh_env__ as env
from xonsh.tools import XonshError

from .env import envDir, projectDir, envRootDir, ensureEnv, getAllEnvs, useEnv


_BASIC_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import projectDir, envDir
print("-- {env_name} {hook}")
"""

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

PREACTIVATE_XONSH = _BASIC_XONSH
POSTACTIVATE_XONSH = _BASIC_XONSH
PREDEACTIVATE_XONSH = _BASIC_XONSH
POSTDEACTIVATE_XONSH = _BASIC_XONSH
GET_ENV_DETAILS_XONSH = _BASIC_XONSH
PRERMVIRTUALENV_XONSH = _BASIC_XONSH
POSTRMVIRTUALENV_XONSH = _BASIC_XONSH


# {script_prefix: (script_basename: script_template)
_hook_scripts = {s: ("{}.xonsh".format(s), "{}_XONSH".format(s.upper()))
                   for s in ["preactivate", "activate", "postactivate",
                             "predeactivate", "postdeactivate",
                             "prermvirtualenv", "postrmvirtualenv",
                             "get_env_details"]}


def _concreteHookPath(hook, hook_d):
    return Path(hook_d) / "bin" / Path(_hook_scripts[hook][0])


def runHookScript(script, env_d=None):
    if script == "deactivate" and "deactivate" in builtins.aliases:
        try:
            builtins.aliases['deactivate']([])
        except Exception as ex:
            print("{} error:\n{}".format(script, ex), file=sys.stderr)
        return

    if not env_d:
        if not envDir():
            raise RuntimeError("No VIRTUAL_ENV active")
        env_d = Path(envDir())
    else:
        env_d = Path(env_d)

    hook_path = env_d / "bin" / Path(_hook_scripts[script][0])
    hook_script = _concreteHookPath(script, env_d)
    if hook_script.exists():
        try:
            builtins.aliases['source']([str(hook_script)])
        except Exception as ex:
            print("{} error:\n{}".format(hook_script, ex), file=sys.stderr)


def activate(env_d):
    env_d = Path(useEnv(env_d))

    subst = {"env_d": str(env_d),
             "predeactivate": str(_concreteHookPath("predeactivate", env_d)),
             "postdeactivate": str(_concreteHookPath("postdeactivate", env_d)),
             "env_name": env_d.parts[-1],
            }
    for hook in _hook_scripts:
        script = _concreteHookPath(hook, env_d)
        templ = _hook_scripts[hook][1]
        subst["hook"] = hook
        # Install templates if not already existing
        if not script.exists():
            with script.open("w") as file:
                file.write(globals()[templ].format(**subst))

    env["VIRTUAL_ENV"] = str(env_d)
    builtins.projectDir = projectDir
    builtins.envDir = envDir

    runHookScript("preactivate")
    runHookScript("activate")
    runHookScript("postactivate")


@ensureEnv
def cdproject(args=None, stdin=None):
    parser = ArgumentParser(prog="showvirtualenv")
    parser.add_argument("--set", dest="set_dir", default=None, type=Path,
                        metavar="DIR", help="Set the project directory.")
    parser.add_argument("-s", "--show", dest="show", action="store_true",
                        help="Echo the project directory.")
    parser.add_argument("-q", dest="quiet", action="store_true",
                        help="No output message for missing .project file.")
    args = parser.parse_args(args)

    project_file = Path(envDir()) / ".project"
    if args.set_dir:
        with project_file.open("w") as fp:
            fp.write(str(args.set_dir))

    if project_file.exists():
        with project_file.open() as fp:
            project_dir = fp.read().strip()

        if args.show:
            print(project_dir)

        # cd to project dir
        _, cdresult_err = builtins.aliases["cd"]([project_dir])
        if cdresult_err:
            raise XonshError(cdresult_err)
    elif not args.quiet:
        print("No project set in {}".format(project_file), file=sys.stderr)


@ensureEnv
def cdvirtualenv(args, stdin=None):
    builtins.aliases["cd"]([envDir()])


@ensureEnv
def cdsitepackages(args, stdin=None):
    env_d = Path(envDir()) / "lib"
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
            runHookScript("get_env_details", Path(envRootDir()) / venv)
            print()


def cpvirtualenv(args, stdin=None):
    # TODO
    print("cpvirtualenv")

def rmvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="rmvirtualenv")
    parser.add_argument("env_names", nargs='+',
                        help="The virtualenvs to remove.")

    args = parser.parse_args(args)
    active_env_d = Path(envDir()) if envDir() else None

    for env_name in args.env_names:
        env_d = Path(useEnv(env_name))
        if env_d == active_env_d:
            print("virtualenv '{}' is currently active, not removing."
                  .format(env_d))
            continue

        runHookScript("prermvirtualenv", env_d)
        print("Removing {}".format(env_d.parts[-1]))
        shutil.rmtree(str(env_d))
        runHookScript("postrmvirtualenv", env_d)


def showvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="showvirtualenv")
    parser.add_argument("env_name", nargs='?', default=None,
                        help="If not specified the currently active env is "
                             "used.")

    args = parser.parse_args(args)
    env_d = Path(useEnv(args.env_name))
    runHookScript("get_env_details", env_d)


def mkvirtualenv(args, stdin=None):
    proc = subprocess.Popen(["virtualenv", "--help"], universal_newlines=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError("Unable to run virtualenv: " + stderr)

    # FIXME: ArgumentParser is formatted epilog, want it untouched
    parser = ArgumentParser(prog="mkvirtualenv", epilog=stdout)
    if len(args) > 1:
        # Move the env_name postiion for argparse finds it first rather than
        # put in the virutalenv opts.
        args = [args[-1]] + args[:-1]
    parser.add_argument("env_name", nargs=1)
    parser.add_argument("-a", action="store", dest="project_path")
    parser.add_argument("-i", action="append", dest="install_pkgs", default=[])
    parser.add_argument("-r", action="append", dest="req_files", default=[])

    args, venv_args  = parser.parse_known_args(args)

    env_d = Path(envRootDir()) / args.env_name[0]
    if env_d.exists():
        return None, "virutalenvs exists: {}".format(env_d)

    proc = subprocess.Popen(["virtualenv"] + venv_args + [str(env_d)])
    result = proc.wait()
    if result != 0:
        return 1

    from .workon import workon
    workon([env_d.parts[-1]])

    if args.project_path:
        cdproject(["--set", args.project_path])

    popen_env = {"PATH": ":".join(env["PATH"])}
    for pkg in args.install_pkgs:
        subprocess.Popen("pip install -U {}".format(pkg), shell=True,
                         env=popen_env).wait()

    for req in args.req_files:
        subprocess.Popen("pip install -r {}".format(req), shell=True,
                         env=popen_env).wait()


@ensureEnv
def editvirtualenv(args, stdin=None):
    # TODO
    env_d = Path(envDir())
    print("TODO", env_d)


_helpers = {
        "cdproject": cdproject,
        "cdvirtualenv": cdvirtualenv,
        "cdsitepackages": cdsitepackages,
        "lsvirtualenv": lsvirtualenv,
        "showvirtualenv": showvirtualenv,
        "rmvirtualenv": rmvirtualenv,
        #"cpvirtualenv": cpvirtualenv,
        "mkvirtualenv": mkvirtualenv,
        #"editvirtualenv": editvirtualenv,
        }

for name, func in _helpers.items():
    builtins.aliases[name] = func
