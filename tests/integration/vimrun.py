"""Helpers for running real headless Vim against a temporary org file.

These tests deliberately do not use the fake tests/vim.py. Every test starts
a fresh Vim subprocess, so no state leaks between tests and nothing here
needs the fake ``vim`` module on sys.path.
"""

import json
import os
import re
import shutil
import subprocess
import textwrap

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TIMEOUT = 60

# lines Vim may legitimately print while loading the plugin
EXPECTED_OUTPUT = ("Speeddating plugin not installed",)


def _vim_has_python3():
    vim = shutil.which("vim")
    if not vim:
        return False
    try:
        out = subprocess.run(
            [vim, "--version"], capture_output=True, text=True, timeout=TIMEOUT
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return "+python3" in out


HAVE_VIM = _vim_has_python3()

PROBE_TEMPLATE = """\
import json, traceback
import vim
result = {{}}
try:
{body}
except BaseException:
    result['__traceback__'] = traceback.format_exc()
with open({outpath!r}, 'w', encoding='utf-8') as _f:
    json.dump(result, _f)
"""


class VimRun:
    def __init__(self, result, output, returncode):
        self.result = result
        self.output = output
        self.returncode = returncode

    def __getitem__(self, key):
        return self.result[key]


def run_vim(
    tmp_path,
    org_text,
    probe,
    vim_cmds=(),
    pre_cmds=(),
    name="test.org",
    filetype_cmd="filetype plugin indent on",
):
    """Open ``org_text`` as an org file in headless Vim and run ``probe``.

    ``probe`` is the body of a Python snippet executed with ``py3file`` after
    the file is loaded. It has ``vim`` and a ``result`` dict in scope; every
    value stored in ``result`` is returned (as JSON) to the test.

    The test fails if Vim did not run the probe to completion, if the probe
    raised, or if Vim printed anything that looks like a Python error.
    """
    org = tmp_path / name
    org.write_text(org_text, encoding="utf-8")
    probe_py = tmp_path / "probe.py"
    out_json = tmp_path / "result.json"
    vim_out = tmp_path / "vim_output.txt"

    body = textwrap.indent(textwrap.dedent(probe), "    ")
    probe_py.write_text(
        PROBE_TEMPLATE.format(body=body, outpath=str(out_json)), encoding="utf-8"
    )

    cmd = [
        shutil.which("vim"),
        "-u",
        "NONE",
        "-N",
        "-es",
        "-i",
        "NONE",
        "--cmd",
        "set rtp^=%s" % REPO,
        "--cmd",
        filetype_cmd,
    ]
    for c in pre_cmds:
        cmd += ["--cmd", c]
    cmd += ["-c", "redir! > %s" % vim_out, "-c", "e %s" % org]
    for c in vim_cmds:
        cmd += ["-c", c]
    cmd += ["-c", "py3file %s" % probe_py, "-c", "redir END", "-c", "qa!"]

    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL
    )
    output = (
        vim_out.read_text(encoding="utf-8", errors="replace")
        if vim_out.exists()
        else ""
    )
    output += proc.stdout + proc.stderr

    # -es can swallow errors, so check for evidence of them explicitly
    for line in output.splitlines():
        if any(e in line for e in EXPECTED_OUTPUT):
            continue
        assert "Traceback" not in line and "Error" not in line, (
            "Vim reported an error:\n" + output
        )
        assert not re.match(r"E\d+:", line), "Vim reported an error:\n" + output
    assert "Traceback" not in output, "Vim reported an error:\n" + output
    assert out_json.exists(), (
        "probe did not complete (Vim failed silently?). Output:\n" + output
    )
    result = json.loads(out_json.read_text(encoding="utf-8"))
    assert "__traceback__" not in result, result["__traceback__"]
    return VimRun(result, output, proc.returncode)
