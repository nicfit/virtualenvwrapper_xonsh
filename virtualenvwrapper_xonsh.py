# -*- coding: utf-8 -*-
import os
import sys
import shutil
import builtins
import subprocess
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from os.path import expandvars, expanduser
from builtins import __xonsh_env__ as env
from xonsh.tools import TERM_COLORS, get_app_color


DEFAULT_VENV_DIR = "~/.virtualenvs"

ENV_REQ_MSG = """A virtualenv is not appear to be active.
See `workon --help` and/or `mkvirtualenv --help` for more details."""

_BASIC_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import projectDir, envDir
print("-- {env_name} {hook}")
"""

ACTIVATE_XONSH = """#!/usr/bin/env xonsh
import sys
import builtins
from pathlib import Path
from builtins import __xonsh_env__ as env

env_d = Path('{env_d}')
bin_d = Path('{env_d}') / "bin"
predeactivate_script = Path('{predeactivate}')
postdeactivate_script = Path('{postdeactivate}')

$VIRTUAL_ENV = str(env_d)
$VIRTUAL_ENV_PROMPT = '{prompt}'

$PATH.insert(0, str(env_d / 'bin'))

if "PYTHONHOME" in env:
    $_OLD_VIRTUAL_PYTHONHOME = $PYTHONHOME
    del env["PYTHONHOME"]

def _deactivate(args, stdin=None):
    try:
        builtins.aliases['source']([str(predeactivate_script)])
    except Exception as ex:
        print("%s: %s" % (postdeactivate_script.parts[-1], ex))

    if str(bin_d) in $PATH:
        $PATH.remove(str(bin_d))
    if "_OLD_VIRTUAL_PYTHONHOME" in env:
        $PYTHONHOME = $_OLD_VIRTUAL_PYTHONHOME

    try:
        builtins.aliases['source']([str(postdeactivate_script)])
    except Exception as ex:
        print("%s: %s" % (postdeactivate_script.parts[-1], ex))

    del env['VIRTUAL_ENV']
    if 'VIRTUAL_ENV_PROMPT' in env:
        del env['VIRTUAL_ENV_PROMPT']
    del builtins.aliases['deactivate']

builtins.aliases['deactivate'] = _deactivate
"""

PREACTIVATE_XONSH = _BASIC_XONSH
POSTACTIVATE_XONSH = _BASIC_XONSH
PREDEACTIVATE_XONSH = _BASIC_XONSH
POSTDEACTIVATE_XONSH = _BASIC_XONSH
GET_ENV_DETAILS_XONSH = _BASIC_XONSH
PRERMVIRTUALENV_XONSH = _BASIC_XONSH
POSTRMVIRTUALENV_XONSH = _BASIC_XONSH
PREMKVIRTUALENV_XONSH = _BASIC_XONSH
POSTMKVIRTUALENV_XONSH = _BASIC_XONSH
PRECPVIRTUALENV_XONSH = _BASIC_XONSH
POSTCPVIRTUALENV_XONSH = _BASIC_XONSH


# {script_prefix: (script_basename: script_template)
_hook_scripts = {s: ("{}.xonsh".format(s), "{}_XONSH".format(s.upper()))
                   for s in ["preactivate", "activate", "postactivate",
                             "predeactivate", "postdeactivate",
                             "prermvirtualenv", "postrmvirtualenv",
                             "premkvirtualenv", "postmkvirtualenv",
                             "precpvirtualenv", "postcpvirtualenv",
                             "get_env_details"]}

class Error(RuntimeError):
    pass

def _success(stdout=None, stderr=None):
    return (stdout, stderr, 0)

def _error(sterr=None, returncode=1):
    return (None, stderr, returncode)

### Decorators ###

def alias(func):
    builtins.aliases[func.__name__] = func
    def wrapper(args, stdin=None):
        try:
            return func(args, stdin=stdin)
        except Error as err:
            return _error(str(err))
    return func


def ensureEnv(func):
    '''Decorator for ensuring a VIRTUAL_ENV is set.'''
    def wrap(*args, **kwargs):
        if envDir() is None:
            raise Error(ENV_REQ_MSG)
        else:
            return func(*args, **kwargs)
    return wrap

### Hook functions ###

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
            raise Error("No VIRTUAL_ENV active")
        env_d = envDir()
    else:
        env_d = Path(env_d)

    hook_path = env_d / "bin" / Path(_hook_scripts[script][0])
    hook_script = _concreteHookPath(script, env_d)
    if hook_script.exists():
        try:
            builtins.aliases['source']([str(hook_script)])
        except Exception as ex:
            print("{} error:\n{}".format(hook_script, ex), file=sys.stderr)


def envDir():
    '''Return the virtualenv root directory or None if not set.'''
    if ("VIRTUAL_ENV" not in env) or not env["VIRTUAL_ENV"]:
        return None
    else:
        return Path(env["VIRTUAL_ENV"])


def envRootDir():
    '''The directory where virtualenv are stored/created. If the root cannot be
    determined and Error exception is raise.'''
    for var in ['VIRTUALENVWRAPPER_XONSH_DIR', 'VIRTUALENVWRAPPER_HOOK_DIR']:
        if var in env:
            root_dir = Path(expandvars(expanduser(env[var])))
            if root_dir.is_dir():
                return root_dir
            else:
                print("{} does not exist or not a directory: {}"
                        .format(var, root_dir))

    root_dir = Path(expandvars(expanduser(DEFAULT_VENV_DIR)))
    if root_dir.is_dir():
        env['VIRTUALENVWRAPPER_XONSH_DIR'] = str(root_dir)
        return root_dir

    raise Error("Set $XONSH_VIRTUALENVWRAPPER_DIR to the directory to use "
                "for virtualenvs. {} is the default but does not exist."
                .format(DEFAULT_VENV_DIR))


def projectDir():
    '''Return the project directory or None if not set.'''
    project_file = envDir() / ".project"
    if not project_file.exists():
        print("No {} file".format(str(project_file)))
        return None

    # cd to project dir
    with project_file.open() as fp:
        project_dir = Path(fp.read().strip())
        if not project_dir.exists():
            raise ValueError("Invalid project file: {}".format(project_dir))
    return project_dir


def getAllEnvs():
    '''Returns a list of all virtualenv directories. May raise an Error
    exception if the virtualenvwrapper root direction cannot be determined.'''
    all_envs = []
    for f in envRootDir().iterdir():
        if f.is_dir():
            all_envs.append(f.name)
    return all_envs


def useEnv(env_name):
    if env_name is None:
        if not envDir():
            raise Error(ENV_REQ_MSG)
        env_d = envDir()
    else:
        env_d = envRootDir() / env_name

    if not env_d.exists():
        raise ValueError("virtualenv not found: {}".format(env_d))

    return env_d


def activate(env_d, reinstall=False, prompt=None):
    env_d = Path(useEnv(env_d))
    env_name = env_d.parts[-1]

    subst = {"env_d": str(env_d),
             "predeactivate": str(_concreteHookPath("predeactivate", env_d)),
             "postdeactivate": str(_concreteHookPath("postdeactivate", env_d)),
             "env_name": env_name,
             "prompt": prompt or env_name,
            }
    for hook in _hook_scripts:
        script = _concreteHookPath(hook, env_d)
        templ = _hook_scripts[hook][1]
        subst["hook"] = hook
        # Install templates if not already existing
        if not script.exists() or reinstall:
            with script.open("w") as file:
                file.write(globals()[templ].format(**subst))

    env["VIRTUAL_ENV"] = str(env_d)

    runHookScript("preactivate")
    runHookScript("activate")
    if prompt and env["VIRTUAL_ENV_PROMPT"] != prompt:
        # Use wants at prompt different than what is stashed in activate
        env["VIRTUAL_ENV_PROMPT"] = prompt
    runHookScript("postactivate")

### Aliases ###

@ensureEnv
@alias
def cdproject(args=None, stdin=None):
    parser = ArgumentParser(prog="showvirtualenv")
    parser.add_argument("--set", dest="set_dir", default=None, type=Path,
                        metavar="DIR", help="Set the project directory.")
    parser.add_argument("-s", "--show", dest="show", action="store_true",
                        help="Echo the project directory.")
    parser.add_argument("-q", dest="quiet", action="store_true",
                        help="No output message for missing .project file.")
    args = parser.parse_args(args)

    project_file = envDir() / ".project"
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
            raise Error(cdresult_err)
    elif not args.quiet:
        print("No project set in {}".format(project_file), file=sys.stderr)


@ensureEnv
@alias
def cdvirtualenv(args, stdin=None):
    builtins.aliases["cd"]([str(envDir())])


@ensureEnv
@alias
def cdsitepackages(args, stdin=None):
    env_d = envDir() / "lib"
    pkgs_dir = [f for f in env_d.glob("python*")][0] / 'site-packages'
    builtins.aliases["cd"]([str(pkgs_dir)])


@alias
def lsvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="lsvirtualenv")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-b", action="store_false", dest="longmode",
                       help="Brief mode.", default=True)
    group.add_argument("-l", action="store_true", dest="longmode",
                       help="Long mode.", default=True)
    args = parser.parse_args(args)

    all_envs = getAllEnvs()
    for venv in sorted(all_envs):
        print(venv)
        if args.longmode:
            print("{}".format("=" * len(venv)))
            runHookScript("get_env_details", envRootDir() / venv)
            print()


@alias
def cpvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="cpvirtualenv")
    parser.add_argument("src_env")
    parser.add_argument("dst_env")
    args = parser.parse_args(args)

    src_env = envRootDir() / args.src_env
    dst_env = envRootDir() / args.dst_env
    if not src_env.exists():
        return None, "Source env does not exist: {}".format(args.src_env)
    if dst_env.exists():
        return None, "Destination env already exist: {}".format(args.dst_env)

    runHookScript("precpvirtualenv", src_env)
    runHookScript("premkvirtualenv", src_env)

    print("Copying {} as {}...".format(src_env.parts[-1], dst_env.parts[-1]))
    shutil.copytree(str(src_env), str(dst_env), symlinks=True)

    # Fix up the new activate script
    with (src_env / "bin" / "activate.xonsh").open("r") as fp:
        curr_activate = fp.read()
    with (dst_env / "bin" / "activate.xonsh").open("w") as fp:
        for line in curr_activate.splitlines():
            line = line.replace(str(src_env), str(dst_env))
            if line.startswith("$VIRTUAL_ENV_PROMPT = "):
                line = "$VIRTUAL_ENV_PROMPT = '{}'".format(dst_env.parts[-1])
            fp.write(line + '\n')

    runHookScript("postmkvirtualenv", src_env)
    runHookScript("postcpvirtualenv", src_env)


@alias
def rmvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="rmvirtualenv")
    parser.add_argument("env_names", nargs='+',
                        help="The virtualenvs to remove.")

    args = parser.parse_args(args)
    active_env_d = envDir() if envDir() else None

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


@alias
def showvirtualenv(args, stdin=None):
    parser = ArgumentParser(prog="showvirtualenv")
    parser.add_argument("env_name", nargs='?', default=None,
                        help="If not specified the currently active env is "
                             "used.")

    args = parser.parse_args(args)
    env_d = Path(useEnv(args.env_name))
    runHookScript("get_env_details", env_d)


@alias
def mkvirtualenv(args, stdin=None):
    proc = subprocess.Popen(["virtualenv", "--help"], universal_newlines=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise Error("Unable to run virtualenv: " + stderr)

    parser = ArgumentParser(prog="mkvirtualenv", epilog=stdout,
                            formatter_class=RawDescriptionHelpFormatter)
    if len(args) > 1:
        # Move the env_name postiion for argparse finds it first rather than
        # put in the virtualenv opts.
        args = [args[-1]] + args[:-1]
    parser.add_argument("env_name", nargs=1)
    parser.add_argument("-a", action="store", dest="project_path",
                        help="The full path to the project directory.")
    parser.add_argument("-i", action="append", dest="install_pkgs", default=[],
                        help="Install a package after the environment is "
                             "created. This option may be repeated.")
    parser.add_argument("-r", action="append", dest="req_files", default=[],
                        help="Provide a pip requirements file to install a "
                             "base set of packages into the new environment.")
    parser.add_argument("--prompt", dest="prompt", default=None,
                        help="Provide an alternate prompt for the environment.")

    args, venv_args  = parser.parse_known_args(args)
    if args.prompt:
        venv_args += ["--prompt={}".format(args.prompt)]

    env_d = envRootDir() / args.env_name[0]
    env_name = env_d.parts[-1]
    if env_d.exists():
        return None, "virtualenv exists: {}".format(env_d)

    proc = subprocess.Popen(["virtualenv"] + venv_args + [str(env_d)])
    result = proc.wait()
    if result != 0:
        return 1

    prompt = args.prompt or env_name
    workon([env_name, "--prompt={}".format(args.prompt)])

    if args.project_path:
        cdproject(["--set", args.project_path])

    popen_env = {"PATH": ":".join(env["PATH"])}
    for pkg in args.install_pkgs:
        subprocess.Popen("pip install -U {}".format(pkg), shell=True,
                         env=popen_env).wait()

    for req in args.req_files:
        subprocess.Popen("pip install -r {}".format(req), shell=True,
                         env=popen_env).wait()


@alias
def workon(args, stdin=None):
    desc = "Deactivate any currently activated virtualenv and activate the "\
           "named environment, triggering any hooks in the process."

    env_d = envRootDir()

    parser = ArgumentParser('workon', description=desc)
    parser.add_argument("--reinstall", action="store_true",
                        help="Reinstall hook files.")
    parser.add_argument("--prompt", dest="prompt", default=None,
                        help="Provide an alternate prompt for the environment.")
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
    activate(env_d, reinstall=args.reinstall, prompt=args.prompt)
    cdproject(['-q'])


builtins.projectDir = projectDir
builtins.envDir = envDir

### Prompts ###

def _promptVirtualenv():
    p = None
    if "VIRTUAL_ENV" in env and env["VIRTUAL_ENV"]:
        env_name = os.path.basename(env["VIRTUAL_ENV"])
        if "VIRTUAL_ENV_PROMPT" in env and env["VIRTUAL_ENV_PROMPT"]:
            p = env["VIRTUAL_ENV_PROMPT"]
        else:
            p = env_name

    if p:
        c = get_app_color("virtualenvwrapper_xonsh", "prompt")
        n = TERM_COLORS["NO_COLOR"] if c else ""
        return "({c}{p}{n})".format(**locals())
    else:
        return ""

env['FORMATTER_DICT']['virtualenv'] = _promptVirtualenv

def updatePrompt():
    env['PROMPT'] = "{virtualenv}" + env['PROMPT']
