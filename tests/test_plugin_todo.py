


import unittest

import vim

from orgmode.liborgmode.base import Direction
from orgmode.plugins.Todo import Todo
from orgmode.vimbuffer import VimBuffer

counter = 0

class TodoTestCase(unittest.TestCase):
    """Tests all the functionality of the TODO module."""

    def setUp(self):
        # set content of the buffer
        global counter
        counter += 1
        vim.EVALHISTORY = []
        vim.EVALRESULTS = {
                # no org_todo_keywords for b
                'exists("b:org_todo_keywords")': '0',
                # global values for org_todo_keywords
                'exists("g:org_todo_keywords")': '1',
                'g:org_todo_keywords': ['TODO', '|', 'DONE'],
                'exists("g:org_debug")': '0',
                'exists("b:org_debug")': '0',
                'exists("*repeat#set()")': '0',
                'b:changedtick': '%d' % counter,
                "v:count": '0'
                }

        vim.current.buffer[:] = [ i for i in """
* Heading 1
** Text 1
*** Text 2
* Text 1
** Text 1
   some text that is
   no heading

""".split('\n') ]

    # toggle
    def test_toggle_todo_with_no_heading(self):
        # nothing should happen
        vim.current.window.cursor = (1, 0)

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[0], '')
        # and repeat it -> it should not change
        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[0], '')

    def test_todo_toggle_NOTODO(self):
        vim.current.window.cursor = (2, 0)
        vim.current.buffer[1] = '** NOTODO Überschrift 1.1'

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '** TODO NOTODO Überschrift 1.1')

    def test_toggle_todo_in_heading_with_no_todo_state_different_levels(self):
        # level 1
        vim.current.window.cursor = (2, 0)
        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* TODO Heading 1')
        self.assertEqual((2, 0), vim.current.window.cursor)

        # level 2
        vim.current.window.cursor = (3, 0)
        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[2], '** TODO Text 1')

        # level 2
        vim.current.window.cursor = (4, 4)
        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[3], '*** TODO Text 2')
        self.assertEqual((4, 9), vim.current.window.cursor)

    def test_circle_through_todo_states(self):
        # * Heading 1 -->
        # * TODO Heading 1 -->
        # * DONE Heading 1 -->
        # * Heading 1 -->
        # * TODO Heading 1 -->
        # * DONE Heading 1
        vim.current.window.cursor = (2, 6)

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* TODO Heading 1')
        self.assertEqual((2, 11), vim.current.window.cursor)

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* DONE Heading 1')
        self.assertEqual((2, 11), vim.current.window.cursor)

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* Heading 1')
        self.assertEqual((2, 6), vim.current.window.cursor)

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* TODO Heading 1')
        self.assertEqual((2, 11), vim.current.window.cursor)

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* DONE Heading 1')
        self.assertEqual((2, 11), vim.current.window.cursor)

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* Heading 1')
        self.assertEqual((2, 6), vim.current.window.cursor)

    def test_circle_through_todo_states_with_more_states(self):
        # * Heading 1 -->
        # * TODO Heading 1 -->
        # * STARTED Heading 1 -->
        # * DONE Heading 1 -->
        # * Heading 1 -->
        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', 'STARTED', 'DONE',
                '|']
        vim.current.window.cursor = (2, 0)

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* TODO Heading 1')

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* STARTED Heading 1')

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* DONE Heading 1')

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[1], '* Heading 1')

    def test_toggle_todo_with_cursor_in_text_not_heading(self):
        # nothing should happen
        vim.current.window.cursor = (7, 0)
        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[5], '** TODO Text 1')
        self.assertEqual(vim.current.window.cursor, (7, 0))

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[5], '** DONE Text 1')
        self.assertEqual(vim.current.window.cursor, (7, 0))

        Todo.toggle_todo_state()
        self.assertEqual(vim.current.buffer[5], '** Text 1')
        self.assertEqual(vim.current.window.cursor, (7, 0))

    # get_states
    def test_get_states_without_seperator(self):
        """The last element in the todostates shouold be used as DONE-state when no sperator is given"""
        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', 'DONE']
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo, expected_done = ['TODO'], ['DONE']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', 'INPROGRESS', 'DONE']
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo = ['TODO', 'INPROGRESS']
        expected_done = ['DONE']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', 'INPROGRESS',
                'DUMMY', 'DONE']
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo  = ['TODO', 'INPROGRESS', 'DUMMY']
        expected_done = ['DONE']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

    def test_get_states_with_seperator(self):
        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', '|', 'DONE']
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo = ['TODO']
        expected_done = ['DONE']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', 'INPROGRESS', '|',
                'DONE']
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo = ['TODO', 'INPROGRESS']
        expected_done = ['DONE']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', 'INPROGRESS',
                'DUMMY', '|',  'DONE']
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo = ['TODO', 'INPROGRESS', 'DUMMY']
        expected_done = ['DONE']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', 'INPROGRESS',
                'DUMMY', '|', 'DELEGATED', 'DONE']
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo =['TODO', 'INPROGRESS', 'DUMMY']
        expected_done = ['DELEGATED', 'DONE']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

        vim.EVALRESULTS['g:org_todo_keywords'] = ['TODO', '|', 'DONEX',
                'DUMMY', 'DELEGATED', 'DONE']
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo = ['TODO']
        expected_done = ['DONEX', 'DUMMY', 'DELEGATED', 'DONE']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

        vim.EVALRESULTS['g:org_todo_keywords'] = [['TODO(t)', '|', 'DONEX'],
                ['DUMMY', 'DELEGATED', 'DONE']]
        states_todo, states_done = VimBuffer().get_todo_states()[0]
        expected_todo = ['TODO']
        expected_done = ['DONEX']
        self.assertEqual(states_todo, expected_todo)
        self.assertEqual(states_done, expected_done)

    # get_next_state
    def test_get_next_state_with_no_current_state(self):
        states = [(('TODO', ), ('DONE', ))]
        current_state = ''
        self.assertEqual(Todo._get_next_state(current_state, states), 'TODO')

        states = [(('TODO', 'NEXT'), ('DELEGATED', 'DONE'))]
        self.assertEqual(Todo._get_next_state(current_state, states), 'TODO')

        states = [(('NEXT', ), ('DELEGATED', 'DONE'))]
        self.assertEqual(Todo._get_next_state(current_state, states), 'NEXT')

    def test_get_next_state_backward_with_no_current_state(self):
        states = [(('TODO', ), ('DONE', ))]
        current_state = ''
        self.assertEqual(Todo._get_next_state(current_state, states,
                Direction.BACKWARD), 'DONE')

        states = [(('TODO', 'NEXT'), ('DELEGATED', 'DONE'))]
        self.assertEqual(Todo._get_next_state(current_state, states,
                Direction.BACKWARD), 'DONE')

        states = [(('NEXT', ), ('DELEGATED', 'DONE'))]
        self.assertEqual(Todo._get_next_state(current_state, states,
                Direction.BACKWARD), 'DONE')

    def test_get_next_state_with_invalid_current_state(self):
        states = [(('TODO', ), ('DONE', ))]
        current_state = 'STI'
        self.assertEqual(Todo._get_next_state(current_state, states), 'TODO')

        states = [(('TODO', 'NEXT'), ('DELEGATED', 'DONE'))]
        self.assertEqual(Todo._get_next_state(current_state, states), 'TODO')

        states = [(('NEXT', ), ('DELEGATED', 'DONE'))]
        self.assertEqual(Todo._get_next_state(current_state, states), 'NEXT')

    def test_get_next_state_backward_with_invalid_current_state(self):
        states = [(('TODO', ), ('DONE', ))]
        current_state = 'STI'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'DONE')

        states = [(('TODO', 'NEXT'), ('DELEGATED', 'DONE'))]
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'DONE')

        states = [(('NEXT', ), ('DELEGATED', 'DONE'))]
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'DONE')

    def test_get_next_state_with_current_state_equals_todo_state(self):
        states = [(('TODO', 'NEXT', 'NOW'), ('DELEGATED', 'DONE'))]
        current_state = 'TODO'
        self.assertEqual(Todo._get_next_state(current_state, states), 'NEXT')

        current_state = 'NEXT'
        self.assertEqual(Todo._get_next_state(current_state, states), 'NOW')

    def test_get_next_state_backward_with_current_state_equals_todo_state(self):
        states = [(('TODO', 'NEXT', 'NOW'), ('DELEGATED', 'DONE'))]
        current_state = 'TODO'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, None)

    def test_get_next_state_backward_misc(self):
        states = [(('TODO', 'NEXT', 'NOW'), ('DELEGATED', 'DONE'))]
        current_state = 'DONE'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'DELEGATED')

        current_state = 'DELEGATED'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'NOW')

        current_state = 'NOW'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'NEXT')

        current_state = 'NEXT'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'TODO')

        current_state = 'TODO'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, None)

        current_state = None
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'DONE')

    def test_get_next_state_with_jump_from_todo_to_done(self):
        states = [(('TODO', 'NEXT', 'NOW'), ('DELEGATED', 'DONE'))]
        current_state = 'NOW'
        self.assertEqual(Todo._get_next_state(current_state, states), 'DELEGATED')

    def test_get_next_state_with_jump_from_done_to_todo(self):
        states = [(('TODO', 'NEXT', 'NOW'), ('DELEGATED', 'DONE'))]
        current_state = 'DONE'
        self.assertEqual(Todo._get_next_state(current_state, states), None)

    def test_get_next_state_in_current_sequence(self):
        states = [(('TODO', 'NEXT', 'NOW'), ('DELEGATED', 'DONE')), (('QA', ), ('RELEASED', ))]
        current_state = 'QA'
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD)
        self.assertEqual(result, 'RELEASED')

    def test_get_next_state_in_current_sequence_with_access_keys(self):
        states = [(('TODO(t)', 'NEXT(n)', 'NOW(w)'), ('DELEGATED(g)', 'DONE(d)')), (('QA(q)', ), ('RELEASED(r)', ))]
        current_state = 'QA'
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD)
        self.assertEqual(result, 'RELEASED')

        current_state = 'NEXT'
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD)
        self.assertEqual(result, 'NOW')

        current_state = 'TODO'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, None)

        current_state = None
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD)
        self.assertEqual(result, 'RELEASED')

    def test_get_next_keyword_sequence(self):
        states = [(('TODO(t)', 'NEXT(n)', 'NOW(w)'), ('DELEGATED(g)', 'DONE(d)')), (('QA(q)', ), ('RELEASED(r)', ))]
        current_state = None
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD, next_set=True)
        self.assertEqual(result, 'TODO')

        current_state = None
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD, next_set=True)
        self.assertEqual(result, 'QA')

        current_state = 'TODO'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD, next_set=True)
        self.assertEqual(result, None)

        current_state = 'TODO'
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD, next_set=True)
        self.assertEqual(result, 'QA')

        current_state = 'NOW'
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD, next_set=True)
        self.assertEqual(result, 'QA')

        current_state = 'DELEGATED'
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD, next_set=True)
        self.assertEqual(result, 'QA')

        current_state = 'QA'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD, next_set=True)
        self.assertEqual(result, 'TODO')

        current_state = 'QA'
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD, next_set=True)
        self.assertEqual(result, None)

        current_state = 'RELEASED'
        result = Todo._get_next_state(current_state, states,
                Direction.FORWARD, next_set=True)
        self.assertEqual(result, None)

        current_state = 'RELEASED'
        result = Todo._get_next_state(current_state, states,
                Direction.BACKWARD, next_set=True)
        self.assertEqual(result, 'TODO')
