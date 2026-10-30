
import unittest

import vim

from orgmode._vim import ORGMODE

PLUGIN_NAME = 'EditCheckbox'

bufnr = 10

def set_vim_buffer(buf=None, cursor=(2, 0), bufnr=0):
    if buf is None:
        buf = []
    vim.current.buffer[:] = buf
    vim.current.window.cursor = cursor
    vim.current.buffer.number = bufnr


counter = 0
class EditCheckboxTestCase(unittest.TestCase):
    def setUp(self):
        if PLUGIN_NAME not in ORGMODE.plugins:
            ORGMODE.register_plugin(PLUGIN_NAME)
        self.editcheckbox = ORGMODE.plugins[PLUGIN_NAME]
        vim.EVALRESULTS = {
                # no org_todo_keywords for b
                'exists("b:org_todo_keywords")': '0',
                # global values for org_todo_keywords
                'exists("g:org_todo_keywords")': '1',
                'g:org_todo_keywords': ['TODO', '|', 'DONE'],
                'exists("g:org_improve_split_heading")': '0',
                'exists("b:org_improve_split_heading")': '0',
                'exists("g:org_debug")': '0',
                'exists("b:org_debug")': '0',
                'exists("*repeat#set()")': '0',
                'b:changedtick': '%d' % counter,
                '&ts': '8',
                'exists("g:org_tag_column")': '0',
                'exists("b:org_tag_column")': '0',
                "v:count": '0',
                # jump to insert mode after adding heading/checkbox
                'exists("g:org_prefer_insert_mode")': '0',
                'exists("b:org_prefer_insert_mode")': '0'}

        self.c1 = """
* heading1 [%]
  - [ ] checkbox1 [/]
        - [ ] checkbox2
        - [ ] checkbox3
              - [ ] checkbox4
  - [ ] checkbox5
        - [ ] checkbox6
              - [ ] checkbox7
              - [ ] checkbox8
""".split('\n')

        self.c2 = """
* a checkbox list [%]
  - checkbox [0%]
        - [ ] test1
        - [ ] test2
        - [ ] test3
""".split('\n')

        self.c3 = """
* heading
  1. [ ] another main task [%]
         - [ ] sub task 1
         - [ ] sub task 2
  2. [ ] another main task
""".split('\n')

        self.c4 = """
* heading
""".split('\n')

        self.c5 = """
* heading1
  1. item
  9. item
  }. item
  a. item
  z. item
  A. item
  Z. item
  aa. item
""".split("\n")

    def test_toggle(self):
        global bufnr
        bufnr += 1
        # test on self.c1
        set_vim_buffer(buf=self.c1, cursor=(6, 0), bufnr=bufnr)
        # update_checkboxes_status
        self.editcheckbox.update_checkboxes_status()
        self.assertEqual(vim.current.buffer[1], "* heading1 [0%]")
        # toggle
        self.editcheckbox.toggle()
        self.assertEqual(vim.current.buffer[5], "              - [X] checkbox4")

        bufnr += 1
        set_vim_buffer(buf=self.c1, cursor=(9, 0), bufnr=bufnr)
        # toggle and check checkbox status
        self.editcheckbox.toggle()
        self.assertEqual(vim.current.buffer[8], "              - [X] checkbox7")
        self.assertEqual(vim.current.buffer[7], "        - [-] checkbox6")
        self.assertEqual(vim.current.buffer[6], "  - [-] checkbox5")

        # new_checkbox
        bufnr += 1
        set_vim_buffer(buf=self.c1, cursor=(9, 0), bufnr=bufnr)
        vim.current.window.cursor = (9, 0)
        self.assertEqual(vim.current.buffer[9], '              - [ ] checkbox8')
        self.editcheckbox.new_checkbox(below=True)
        # vim's buffer behave just opposite to Python's list when inserting a
        # new item.  The new entry is appended in vim put prepended in Python!
        self.assertEqual(vim.current.buffer[10], '              - [ ] checkbox8')
        self.assertEqual(vim.current.buffer[9], '              - [ ] ')
        self.editcheckbox.update_checkboxes_status()

    def test_no_status_checkbox(self):
        global bufnr
        bufnr += 1
        # test on self.c2
        set_vim_buffer(buf=self.c2, bufnr=bufnr)
        self.assertEqual(vim.current.buffer[2], "  - checkbox [0%]")
        # toggle
        vim.current.window.cursor = (4, 0)
        self.editcheckbox.toggle()
        self.assertEqual(vim.current.buffer[3], "        - [X] test1")

        # self.editcheckbox.update_checkboxes_status()
        # see if the no status checkbox update its status
        self.assertEqual(vim.current.buffer[2], "  - checkbox [33%]")

    def test_number_list(self):
        global bufnr
        bufnr += 1
        set_vim_buffer(buf=self.c3, bufnr=bufnr)
        vim.current.window.cursor = (6, 0)
        self.editcheckbox.toggle()
        self.assertEqual(vim.current.buffer[5], "  2. [X] another main task")

    def test_new_checkbox(self):
        global bufnr
        bufnr += 1
        set_vim_buffer(buf=self.c4, bufnr=bufnr)
        vim.current.window.cursor = (2, 1)
        self.editcheckbox.new_checkbox(below=True)
        self.assertEqual(vim.current.buffer[2], "  - [ ] ")

    def test_item_decrement(self):
        global bufnr
        bufnr += 1
        set_vim_buffer(buf=self.c5, bufnr=bufnr)

        vim.current.window.cursor = (3, 1)
        self.editcheckbox.new_checkbox(below=False, plain=True)
        self.assertEqual(vim.current.buffer[2], "  0. ")
        self.assertEqual(vim.current.buffer[3], "  1. item")

        vim.current.window.cursor = (3, 1)
        self.editcheckbox.new_checkbox(below=False, plain=True)
        self.assertEqual(vim.current.buffer[1], "* heading1")
        self.assertEqual(vim.current.buffer[2], "  0. ")
        self.assertEqual(vim.current.buffer[3], "  1. item")

        vim.current.window.cursor = (5, 1)
        self.editcheckbox.new_checkbox(below=False, plain=True)
        self.assertEqual(vim.current.buffer[4], "  8. ")
        self.assertEqual(vim.current.buffer[5], "  9. item")

        vim.current.window.cursor = (8, 1)
        self.editcheckbox.new_checkbox(below=False, plain=True)
        # no further decrement than a
        self.assertEqual(vim.current.buffer[6], "  }. item")
        self.assertEqual(vim.current.buffer[7], "  a. item")
        self.assertEqual(vim.current.buffer[8], "  z. item")

    def test_item_decrementA(self):
        global bufnr
        bufnr += 1
        set_vim_buffer(buf=self.c5, bufnr=bufnr)
        vim.current.window.cursor = (8, 1)
        self.editcheckbox.new_checkbox(below=False, plain=True)
        # decrement from A to z
        self.assertEqual(vim.current.buffer[7], "  z. ")
        self.assertEqual(vim.current.buffer[8], "  A. item")

    def test_item_increment(self):
        global bufnr
        bufnr += 1
        set_vim_buffer(buf=self.c5, bufnr=bufnr)

        vim.current.window.cursor = (3, 1)
        self.editcheckbox.new_checkbox(below=True, plain=True)
        self.assertEqual(vim.current.buffer[2], "  1. item")
        self.assertEqual(vim.current.buffer[3], "  2. ")

        vim.current.window.cursor = (5, 1)
        self.editcheckbox.new_checkbox(below=True, plain=True)
        self.assertEqual(vim.current.buffer[4], "  9. item")
        self.assertEqual(vim.current.buffer[5], "  }. item")
        self.assertEqual(vim.current.buffer[6], "  10. ")

    def test_item_incrementz(self):
        global bufnr
        bufnr += 1
        set_vim_buffer(buf=self.c5, bufnr=bufnr)

        vim.current.window.cursor = (6, 1)
        self.editcheckbox.new_checkbox(below=True, plain=True)
        self.assertEqual(vim.current.buffer[5], "  a. item")
        self.assertEqual(vim.current.buffer[6], "  b. ")

        vim.current.window.cursor = (8, 1)
        self.editcheckbox.new_checkbox(below=True, plain=True)
        self.assertEqual(vim.current.buffer[7], "  z. item")
        self.assertEqual(vim.current.buffer[8], "  A. ")

        vim.current.window.cursor = (11, 1)
        self.editcheckbox.new_checkbox(below=True, plain=True)
        self.assertEqual(vim.current.buffer[10], "  Z. item")
        self.assertEqual(vim.current.buffer[11], "  aa. item")
        self.assertEqual(vim.current.buffer[12], "")

        vim.current.window.cursor = (12, 1)
        self.editcheckbox.new_checkbox(below=True, plain=True)
        self.assertEqual(vim.current.buffer[11], "  aa. item")
        self.assertEqual(vim.current.buffer[12], "")
