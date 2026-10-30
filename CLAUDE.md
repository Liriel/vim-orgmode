# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

vim-orgmode is a Vim filetype plugin implementing Emacs Org-Mode features. Most of it is Python running inside Vim's embedded interpreter. It needs Python 3.10+ and Vim 8.2+ with `+python3`; there is no Python 2 support. User documentation is in `doc/orgguide.txt`; notable changes go in `CHANGELOG.org`.

## Commands

Run everything from the repo root. `tests/conftest.py` puts `ftplugin/` and the fake `tests/vim.py` on `sys.path`.

```sh
pip install --group dev        # pytest, coverage, ruff, sphinx (needs pip >= 25.1)
make test                      # pytest: unit tests, plus integration tests if Vim has +python3
make lint                      # ruff check and ruff format --check
make format                    # ruff format
make coverage                  # coverage run -m pytest, then report and htmlcov/
make docs                      # Sphinx in ftplugin/orgmode/docs, warnings are errors
make clean                     # caches, coverage data, docs build
pytest tests/test_plugin_todo.py::TodoTestCase::test_toggle_todo_with_no_heading   # one test
```

- New test modules (`tests/test_*.py`) are discovered automatically; nothing to register.
- Integration tests in `tests/integration/` run a headless real Vim and are skipped when no Vim with `+python3` is found. `REQUIRE_VIM=1` turns that skip into a failure, `REQUIRE_LOCALE=1` does the same for the locale in `test_liborgdate_utf8.py` (both are set in CI).
- CI is `.github/workflows/ci.yml`: lint, unit tests on Python 3.10-3.14, integration tests, docs.

## Architecture

**Startup.** `ftplugin/org.vim` checks for Vim 8.2 with `+python3`, adds `ftplugin/` to `sys.path`, and calls `ORGMODE.start()` once per Vim session (guarded by `g:loaded_org`). The buffer-local part of the file reruns for each org buffer and re-registers keybindings.

**Layers**, under `ftplugin/orgmode/`:

- `liborgmode/` is the document model: `Document`, `Heading`, `Checkbox` (the latter two share `DomObj`/`DomObjList`) and the `OrgDate` types. It isn't fully Vim-free, as several of its modules `import vim`.
- `vimbuffer.py` holds `VimBuffer(Document)`, which binds the model to a real Vim buffer, and `VimBufferContent`, which wraps the Vim buffer in a `MultiPurposeList` so changes go to the real buffer.
- `_vim.py` holds the `ORGMODE` singleton, which loads plugins and caches one document per buffer number, plus the decorators `apply_count`, `repeat` and `realign_tags`, and the fold and indent callbacks.
- `plugins/` holds the features. The names in `g:org_plugins` are loaded by name, and order matters because it sets the menu order; `'|'` adds a menu separator.

**Plugin contract.** A plugin is a class with the same name as its module in `plugins/`. It has `self.menu` and `self.keybindings`, and a `register()` method that fills them with `Keybinding(key, Plug(name, command))` and `ActionEntry` objects. The command strings call back into Python, e.g. `'%s ORGMODE.plugins["ShowHide"].toggle_folding()<CR>' % VIM_PY_CALL`. Decorators on `ORGMODE.register_plugin` then create the actual mappings, commands and menu entries from those attributes. Plugin actions decorated with `@repeat` return the `<Plug>` name to repeat.

**Editing a document.** Get the document with `ORGMODE.get_document()`, change `Heading` objects, then call `d.write()`. Writes are incremental: DOM objects track dirty state (`is_dirty`, `is_dirty_body`) and their original positions (`_orig_start`), and only the changed lines are written back. The cached document is reused only while `b:changedtick` matches, otherwise the DOM is rebuilt. `allow_dirty=True` skips that rebuild, which is what the fold callbacks use for speed.

**Settings.** Read options with `orgmode.settings.get()`, which checks `b:` before `g:`.

## Traps

- Slices of `MultiPurposeList` (and so `DomObjList`/`HeadingList`) deliberately return plain lists. Returning a new instance of the subclass re-associates the headings and detaches them from their document, which once made `new_heading` wipe the buffer.
- `VimBuffer.write()` raises `ValueError` for a dirty heading with no start position, rather than replacing the whole buffer. If you hit that, the DOM is broken; don't work around the check.

## Testing plugins

`tests/vim.py` replaces the Vim API. `vim.eval()` only returns what is in the `vim.EVALRESULTS` dict, keyed by the exact expression, and `vim.command()` just records to `CMDHISTORY`. Consequently:

- Any new `vim.eval()` call in the code needs a matching `EVALRESULTS` entry in the tests, or it returns `None`.
- `tests/conftest.py` has an autouse fixture that resets the fake's `EVALHISTORY`, `EVALRESULTS` (to the defaults), `CMDHISTORY`, `CMDRESULTS` and `vim.current` and clears the `ORGMODE` document cache before every test, so a stale cached document can no longer leak between tests. Existing tests still set a fresh `b:changedtick` from a counter in `setUp`; that is no longer needed for isolation, but a test that edits the buffer and calls `get_document()` again within one test still needs a new value to force a rebuild.
- Tests set `vim.current.buffer[:]` and `vim.current.window.cursor` directly.
- Mappings and real folding are not exercised by the fake. `tests/integration/` runs the plugin in a real Vim for load, new heading, promote/demote, TODO toggle, folding and the agenda; use it for behaviour the fake can't show (the fake once hid the data-loss bug).
