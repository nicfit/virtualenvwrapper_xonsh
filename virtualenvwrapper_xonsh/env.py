# -*- coding: utf-8 -*-
import builtins
from pathlib import Path
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
