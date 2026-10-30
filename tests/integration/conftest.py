import os

import pytest
from vimrun import HAVE_VIM


@pytest.fixture(autouse=True)
def require_vim():
    """Skip when there is no Vim with +python3, unless REQUIRE_VIM is set.

    CI sets REQUIRE_VIM=1 so that a missing Vim fails the job instead of
    silently skipping every integration test.
    """
    if HAVE_VIM:
        return
    msg = "vim with +python3 not available"
    if os.environ.get("REQUIRE_VIM"):
        pytest.fail(msg + " (REQUIRE_VIM is set)")
    pytest.skip(msg)
