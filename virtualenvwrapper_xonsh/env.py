# -*- coding: utf-8 -*-
import builtins
from pathlib import Path
from builtins import __xonsh_env__ as env


def env_dir():
    if ("VIRTUAL_ENV" not in env) or not env["VIRTUAL_ENV"]:
        return None
    else:
        return env["VIRTUAL_ENV"]


def project_dir():
    project_file = Path(env_dir()) / ".project"
    if not project_file.exists():
        print("No {} file".format(str(project_file)))

    # cd to project dir
    with project_file.open() as fp:
        project_dir = Path(fp.read().strip())
        if not project_dir.exists():
            raise ValueError("Invalid project file: {}".format(project_dir))
    return project_dir

