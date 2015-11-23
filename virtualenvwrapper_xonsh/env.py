# -*- coding: utf-8 -*-
import builtins
import subprocess
from pathlib import Path
from argparse import ArgumentParser
from builtins import __xonsh_env__ as env


def ensureEnv(func):
    '''Decorator for ensuring a VIRTUAL_ENV is set.'''
    msg = "no virtualenv active, or active virtualenv is missing"
    def wrap(*args, **kwargs):
        if env_dir() is None:
            raise RuntimeError(msg)
        else:
            return func(*args, **kwargs)
    return wrap


def env_dir():
    '''Return the virutalenv root directory or None if not set.'''
    if ("VIRTUAL_ENV" not in env) or not env["VIRTUAL_ENV"]:
        return None
    else:
        return env["VIRTUAL_ENV"]


def env_root_dir():
    '''The directory where virutalenvs are created/maintained.'''
    if "VIRTUALENVWRAPPER_HOOK_DIR" not in env:
        raise RuntimeError("virtualenvwrapper variable "
                           "$VIRTUALENVWRAPPER_HOOK_DIR not defined")
    root_dir = Path(env["VIRTUALENVWRAPPER_HOOK_DIR"])
    return str(root_dir)


def project_dir():
    '''Return the project directory or None if not set.'''
    project_file = Path(env_dir()) / ".project"
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
    '''Returns a list of all virtualenv directories.'''
    all_envs = []
    for f in Path(env_root_dir()).iterdir():
        if f.is_dir():
            all_envs.append(f.name)
    return all_envs


def useEnv(env_name):
    if env_name is None:
        if not env_dir():
            raise RuntimeError("No active virtualenv set, please specify an "
                               "environment.")
        env_d = Path(env_dir())
    else:
        env_d = Path(env_root_dir()) / env_name

    if not env_d.exists():
        raise RuntimeError("virtualenv not found: {}".format(env_d))

    return str(env_d)


def mkvirtualenv(args, stdin=None):
    proc = subprocess.Popen(["virtualenv", "--help"], universal_newlines=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError("Unable to run virtualenv: " + stderr)

    # FIXME: ArgumentParser is formatted epilog, want it untouched
    parser = ArgumentParser(prog="mkvirtualenv", epilog=stdout)
    parser.add_argument("env_name")

    args = parser.parse_args(args)

    import ipdb; ipdb.set_trace()
