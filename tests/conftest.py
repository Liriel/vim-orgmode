"""Shared pytest setup for the unit tests.

The plugin is normally run inside Vim, where ``import vim`` and ``orgmode``
(from ftplugin/) are available. Outside Vim the tests put ftplugin/ on
sys.path and use the fake ``vim`` module from tests/vim.py.

The integration tests in tests/integration start a real Vim in a subprocess
and are not affected by any of this.
"""
import copy
import os
import sys

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FTPLUGIN_DIR = os.path.join(os.path.dirname(TESTS_DIR), 'ftplugin')

# tests/ first so that ``import vim`` finds the fake
for path in (FTPLUGIN_DIR, TESTS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import vim  # noqa: E402  (the fake, see above)

_DEFAULT_EVALRESULTS = copy.deepcopy(vim.EVALRESULTS)


@pytest.fixture(autouse=True)
def reset_fake_vim():
    """Give every test a pristine fake vim and a cold ORGMODE document cache.

    The fake keeps its state in module globals and the ORGMODE singleton
    caches documents by buffer number, so without this a test can see what
    an earlier one left behind. Tests that need other values still set them
    in setUp, which runs after this fixture.
    """
    vim.EVALHISTORY = []
    vim.EVALRESULTS = copy.deepcopy(_DEFAULT_EVALRESULTS)
    vim.CMDHISTORY = []
    vim.CMDRESULTS = {}
    vim.current = vim.VimTest()

    orgmode_vim = sys.modules.get('orgmode._vim')
    if orgmode_vim is not None:
        orgmode_vim.ORGMODE._documents.clear()
    yield
