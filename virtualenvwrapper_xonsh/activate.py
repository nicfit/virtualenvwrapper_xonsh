# -*- coding: utf-8 -*-
import builtins
from pathlib import Path
from builtins import __xonsh_env__ as env

from .env import env_dir, project_dir


ACTIVATE_XONSH = """#!/usr/bin/env xonsh
from pathlib import Path
from builtins import __xonsh_env__ as env

env_dir = Path('{env_dir}')
$VIRTUAL_ENV = str(env_dir)

$_OLD_VIRTUAL_PATH = $PATH
$PATH.insert(0, str(env_dir / "bin"))

if "PYTHONHOME" in env:
    $_OLD_VIRTUAL_PYTHONHOME = $PYTHONHOME
    del env["PYTHONHOME"]

def _deactivate(args, stdin=None):
    predeactivate_script = env_dir / "bin" / Path("predeactivate.xonsh")
    postdeactivate_script = env_dir / "bin" / Path("postdeactivate.xonsh")

    builtins.aliases['source']([str(predeactivate_script)])

    $PATH.remove(str(env_dir / "bin"))
    if "_OLD_VIRTUAL_PYTHONHOME" in env:
        $PYTHONHOME = $_OLD_VIRTUAL_PYTHONHOME

    del builtins.aliases['deactivate']
    builtins.aliases['source']([str(postdeactivate_script)])
    del env["VIRTUAL_ENV"]

builtins.aliases['deactivate'] = _deactivate
"""

PREACTIVATE_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import project_dir, env_dir
"""

POSTACTIVATE_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import project_dir, env_dir
"""

PREDEACTIVATE_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import project_dir, env_dir
"""

POSTDEACTIVATE_XONSH = """#!/usr/bin/env xonsh
from builtins import __xonsh_env__ as env
from builtins import project_dir, env_dir
"""

def activate(env_dir):
    preactivate_script = env_dir / "bin" / Path("preactivate.xonsh")
    activate_script = env_dir / "bin" / Path("activate.xonsh")
    postactivate_script = env_dir / "bin" / Path("postactivate.xonsh")
    predeactivate_script = env_dir / "bin" / Path("predeactivate.xonsh")
    postdeactivate_script = env_dir / "bin" / Path("postdeactivate.xonsh")

    for script in [preactivate_script, postactivate_script, activate_script,
                   predeactivate_script, postdeactivate_script]:
        if not script.exists():
            with script.open("w") as file:
                templ = script.name.upper().replace('.', '_')
                file.write(globals()[templ].format(env_dir=str(env_dir)
                                           .strip()))


    builtins.project_dir = project_dir
    builtins.env_dir = env_dir
    builtins.aliases['source']([str(preactivate_script)])
    builtins.aliases['source']([str(activate_script)])
    builtins.aliases['source']([str(postactivate_script)])


def ensureEnv(func):
    '''Decorator for ensuring a VIRTUAL_ENV is set.'''
    msg = "ERROR: no virtualenv active, or active virtualenv is missing"
    def wrap(*args, **kwargs):
        if env_dir() is None:
            return (None, msg)
        else:
            return func(*args, **kwargs)
    return wrap


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
    env_dir = Path(env_dir()) / "lib"
    pkgs_dir = [f for f in env_dir.glob("python*")][0] / 'site-packages'
    builtins.aliases["cd"]([str(pkgs_dir)])


def cpvirtualenv(args, stdin=None):
    # TODO
    print("cpvirtualenv")
def lsvirtualenv(args, stdin=None):
    # TODO
    print("lsvirtualenv")
def rmvirtualenv(args, stdin=None):
    # TODO
    print("rmvirtualenv")
def mkvirtualenv(args, stdin=None):
    # TODO
    print("mkvirtualenv")


_helpers = {
        "cdproject": cdproject,
        "cdvirtualenv": cdvirtualenv,
        "cdsitepackages": cdsitepackages,
        "cpvirtualenv": cpvirtualenv,
        "lsvirtualenv": lsvirtualenv,
        "rmvirtualenv": rmvirtualenv,
        "mkvirtualenv": mkvirtualenv,
        }

for name, func in _helpers.items():
    builtins.aliases[name] = func
