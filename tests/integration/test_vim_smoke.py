# -*- coding: utf-8 -*-
"""Smoke tests against real headless Vim.

Run with ``pytest tests/integration`` (separately from the unittest suite in
tests/, which uses a fake ``vim`` module).
"""
from datetime import date, timedelta

import pytest

from conftest import HAVE_VIM, run_vim

pytestmark = pytest.mark.skipif(
    not HAVE_VIM, reason='vim with +python3 not available')

NESTED = '* A\nbody a\n** B\nbody b\n* C\nbody c\n'


def test_plugin_loads_and_registers_all_plugins(tmp_path):
    r = run_vim(tmp_path, NESTED, '''
        result['wanted'] = vim.eval('g:org_plugins')
        result['loaded'] = sorted(ORGMODE.plugins.keys())
        result['ft'] = vim.eval('&filetype')
        result['lines'] = list(vim.current.buffer)
    ''', vim_cmds=['py3 from orgmode._vim import ORGMODE'])
    wanted = sorted(p for p in r['wanted'] if p != '|')
    assert r['ft'] == 'org'
    assert r['loaded'] == wanted
    assert len(wanted) == 11
    assert r['lines'] == NESTED.splitlines()


def test_new_heading_below_keeps_children(tmp_path):
    # regression: used to replace the whole buffer with '** B'
    r = run_vim(tmp_path, '* A\nbody a\n** B\nbody b\n* C\nbody c\n', '''
        from orgmode._vim import ORGMODE
        vim.current.window.cursor = (1, 0)
        ORGMODE.plugins['EditStructure'].new_heading(
            below=True, insert_mode=False)
        result['lines'] = list(vim.current.buffer)
    ''')
    assert r['lines'] == ['* A', 'body a', '* ', '** B', 'body b',
                          '* C', 'body c']


def test_new_heading_above(tmp_path):
    r = run_vim(tmp_path, NESTED, '''
        from orgmode._vim import ORGMODE
        vim.current.window.cursor = (5, 0)
        ORGMODE.plugins['EditStructure'].new_heading(
            below=False, insert_mode=False)
        result['lines'] = list(vim.current.buffer)
    ''')
    assert r['lines'] == ['* A', 'body a', '** B', 'body b', '* ', '* C',
                          'body c']


def test_demote_and_promote_heading_with_children(tmp_path):
    r = run_vim(tmp_path, NESTED, '''
        from orgmode._vim import ORGMODE
        es = ORGMODE.plugins['EditStructure']
        vim.current.window.cursor = (1, 0)
        es.demote_heading(including_children=True)
        result['demoted'] = list(vim.current.buffer)
        es.promote_heading(including_children=True)
        result['promoted'] = list(vim.current.buffer)
        vim.current.window.cursor = (3, 0)
        es.promote_heading(including_children=False)
        result['promoted_b'] = list(vim.current.buffer)
    ''')
    assert r['demoted'] == ['** A', 'body a', '*** B', 'body b', '* C',
                            'body c']
    assert r['promoted'] == NESTED.splitlines()
    assert r['promoted_b'] == ['* A', 'body a', '* B', 'body b', '* C',
                               'body c']


def test_toggle_todo(tmp_path):
    r = run_vim(tmp_path, '* A\nbody\n* B\n', '''
        from orgmode._vim import ORGMODE
        todo = ORGMODE.plugins['Todo']
        vim.current.window.cursor = (1, 0)
        states = []
        for _ in range(3):
            todo.toggle_todo_state()
            states.append(vim.current.buffer[0])
        result['states'] = states
        result['lines'] = list(vim.current.buffer)
    ''')
    assert r['states'] == ['* TODO A', '* DONE A', '* A']
    assert r['lines'] == ['* A', 'body', '* B']


def test_fold_levels(tmp_path):
    # exercises the real foldexpr (GetOrgFolding -> fold_orgmode)
    r = run_vim(tmp_path, NESTED, '''
        result['levels'] = [int(vim.eval('foldlevel(%d)' % i))
                            for i in range(1, 7)]
        result['method'] = vim.eval('&foldmethod')
    ''', vim_cmds=['normal! zx'])
    assert r['method'] == 'expr'
    assert r['levels'] == [1, 1, 2, 2, 1, 1]


def _dated(delta_days, with_time):
    d = date.today() + timedelta(days=delta_days)
    s = d.strftime('%Y-%m-%d %a')
    return '<%s%s>' % (s, ' 10:30' if with_time else '')


@pytest.mark.parametrize('with_time', [False, True])
def test_agenda_week_and_todo_views(tmp_path, with_time):
    text = ('* TODO soon\n  %s\n'
            '* TODO later\n  %s\n'
            '* DONE finished\n  %s\n'
            '* TODO undated\n'
            % (_dated(2, with_time), _dated(30, with_time),
               _dated(1, with_time)))
    r = run_vim(tmp_path, text, '''
        from orgmode._vim import ORGMODE
        docs = [ORGMODE.get_document()]
        mgr = ORGMODE.agenda_manager
        result['week'] = [h.title for h in
                          mgr.get_next_week_and_active_todo(docs)]
        result['todo'] = sorted(h.title for h in mgr.get_todo(docs))
        result['timeline'] = [h.title for h in
                              mgr.get_timestamped_items(docs)]
        ag = ORGMODE.plugins['Agenda']
        ag.list_next_week_for_buffer()
        result['agenda_buf'] = list(vim.current.buffer)
    ''')
    assert r['week'] == ['soon']
    assert r['todo'] == ['later', 'soon', 'undated']
    assert r['timeline'] == ['finished', 'soon', 'later']
    shown = '\n'.join(r['agenda_buf'])
    assert r['agenda_buf'][0] == 'Week Agenda:'
    assert 'soon' in shown and 'later' not in shown
