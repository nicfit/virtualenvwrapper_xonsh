=======================
virtualenvwrapper_xonsh
=======================

Quickstart
==========
::
    $ mkdir -p ~/.virtualenvs

    $ git clone https://github.com/nicfit/virtualenvwrapper_xonsh.git
    $ cd ./virtualenvwrapper_xonsh
    $ import sys; sys.path.append('.')
    $ import virtualenvwrapper_xonsh

    $ mkvirtualenv sampleenv
    (sampleenv)$ which python pip
    ~/.virtualenvs/sampleenv/bin/python
    ~/.virtualenvs/sampleenv/bin/pip

    (sampleenv)$ deactivate
    $ which python pip
    /usr/bin/python
    /usr/bin/pip


Introduction
============
Shout out to Doug Hellmann and ``virtualenvwrapper``.

~/.xonshrc
----------
::
    import os, sys
    sys.path.append(os.path.expanduser("~/.xonsh.d"))

    VIRTUALENVWRAPPER_XONSH_DIR = "~/.virtualenvs"
    import virtualenvwrapper_xonsh

Customization
=============

- VIRTUALENVWRAPPER_XONSH_DIR

Xonsh
-----
::
    $ git clone https://github.com/scopatz/xonsh.git
    $ cd xonsh
    $ mkvirtualenv -p /usr/bin/python3.5 -r requirements.txt -i prompt-toolkit xonsh
    (xonsh)$ 

Prompt
======

To show the active virtualenv in your prompt use the ``updatePrompt`` function.

::
    $ import virtualenvwrapper_xonsh
    virtualenvwrapper_xonsh.updatePrompt()

This simply prepends the virtualenv to the beginning of your prompt, so you 
may also choose to use the ``{virtualenv}`` variable in anywhere in you
``$PROMPT`` string.
