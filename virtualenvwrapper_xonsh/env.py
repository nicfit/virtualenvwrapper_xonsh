# -*- coding: utf-8 -*-
import builtins
from pathlib import Path
from argparse import ArgumentParser, REMAINDER
from builtins import __xonsh_env__ as env


def ensureEnv(func):
    '''Decorator for ensuring a VIRTUAL_ENV is set.'''
    msg = "no virtualenv active, or active virtualenv is missing"
    def wrap(*args, **kwargs):
        if envDir() is None:
            raise RuntimeError(msg)
        else:
            return func(*args, **kwargs)
    return wrap


def envDir():
    '''Return the virutalenv root directory or None if not set.'''
    if ("VIRTUAL_ENV" not in env) or not env["VIRTUAL_ENV"]:
        return None
    else:
        return env["VIRTUAL_ENV"]


def envRootDir():
    '''The directory where virutalenvs are created/maintained.'''
    if "VIRTUALENVWRAPPER_HOOK_DIR" not in env:
        raise RuntimeError("virtualenvwrapper variable "
                           "$VIRTUALENVWRAPPER_HOOK_DIR not defined")
    root_dir = Path(env["VIRTUALENVWRAPPER_HOOK_DIR"])
    return str(root_dir)


def projectDir():
    '''Return the project directory or None if not set.'''
    project_file = Path(envDir()) / ".project"
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
    for f in Path(envRootDir()).iterdir():
        if f.is_dir():
            all_envs.append(f.name)
    return all_envs


def useEnv(env_name):
    if env_name is None:
        if not envDir():
            raise RuntimeError("No active virtualenv set, please specify an "
                               "environment.")
        env_d = Path(envDir())
    else:
        env_d = Path(envRootDir()) / env_name

    if not env_d.exists():
        raise RuntimeError("virtualenv not found: {}".format(env_d))

    return str(env_d)
