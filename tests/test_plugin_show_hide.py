# -*- coding: utf-8 -*-

import unittest
import sys

import vim

from orgmode._vim import ORGMODE


counter = 0
class ShowHideTestCase(unittest.TestCase):
    def setUp(self):
        global counter
        counter += 1
        vim.CMDHISTORY = []
        vim.CMDRESULTS = {}
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
                "v:count": '0'}
        if not 'ShowHide' in ORGMODE.plugins:
            ORGMODE.register_plugin('ShowHide')
        self.showhide = ORGMODE.plugins['ShowHide']
        vim.current.buffer[:] = [ i for i in """
* Überschrift 1
Text 1

Bla bla
** Überschrift 1.1
Text 2

Bla Bla bla
** Überschrift 1.2
Text 3

**** Überschrift 1.2.1.falsch

Bla Bla bla bla
*** Überschrift 1.2.1
* Überschrift 2
* Überschrift 3
  asdf sdf
""".split('\n') ]

    def test_no_heading_toggle_folding(self):
        vim.current.window.cursor = (1, 0)
        self.assertEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(vim.EVALHISTORY[-1], 'feedkeys("<Tab>", "n")')
        self.assertEqual(vim.current.window.cursor, (1, 0))

    def test_toggle_folding_first_heading_with_no_children(self):
        vim.current.buffer[:] = [ i for i in """
* Überschrift 1
Text 1

Bla bla
* Überschrift 2
* Überschrift 3
  asdf sdf
""".split('\n') ]
        vim.EVALRESULTS.update({
                'foldclosed(2)': '2',
                'foldclosed(6)': '-1',
                'foldclosed(7)': '-1',
                })
        vim.current.window.cursor = (2, 0)

        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 1zo')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_close_one(self):
        vim.current.window.cursor = (13, 0)
        vim.EVALRESULTS.update({
                'foldclosed(13)': '-1',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 2)
        self.assertEqual(vim.CMDHISTORY[-2], '13,15foldclose!')
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 2zo')
        self.assertEqual(vim.current.window.cursor, (13, 0))

    def test_toggle_folding_open_one(self):
        vim.current.window.cursor = (10, 0)
        vim.EVALRESULTS.update({
                'foldclosed(10)': '10',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 1zo')
        self.assertEqual(vim.current.window.cursor, (10, 0))

    def test_toggle_folding_close_multiple_all_open(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '-1',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '-1',
                'foldclosed(16)': '-1',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], '2,16foldclose!')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_all_closed(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '2',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 1zo')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_first_level_open(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '6',
                'foldclosed(10)': '10',
                'foldclosed(13)': '13',
                'foldclosed(16)': '16',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 2)
        self.assertEqual(vim.CMDHISTORY[-2], 'normal! 6gg1zo')
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 10gg1zo')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_second_level_half_open(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '-1',
                'foldclosed(10)': '10',
                'foldclosed(13)': '13',
                'foldclosed(16)': '16',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 4)
        self.assertEqual(vim.CMDHISTORY[-4], 'normal! 6gg2zo')
        self.assertEqual(vim.CMDHISTORY[-3], 'normal! 10gg2zo')
        self.assertEqual(vim.CMDHISTORY[-2], 'normal! 13gg2zo')
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 16gg2zo')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_other_second_level_half_open(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '6',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '13',
                'foldclosed(16)': '16',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 4)
        self.assertEqual(vim.CMDHISTORY[-4], 'normal! 6gg2zo')
        self.assertEqual(vim.CMDHISTORY[-3], 'normal! 10gg2zo')
        self.assertEqual(vim.CMDHISTORY[-2], 'normal! 13gg2zo')
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 16gg2zo')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_third_level_half_open(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '-1',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '-1',
                'foldclosed(16)': '16',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 4)
        self.assertEqual(vim.CMDHISTORY[-4], 'normal! 6gg3zo')
        self.assertEqual(vim.CMDHISTORY[-3], 'normal! 10gg3zo')
        self.assertEqual(vim.CMDHISTORY[-2], 'normal! 13gg3zo')
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 16gg3zo')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_other_third_level_half_open(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '-1',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '13',
                'foldclosed(16)': '-1',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 4)
        self.assertEqual(vim.CMDHISTORY[-4], 'normal! 6gg3zo')
        self.assertEqual(vim.CMDHISTORY[-3], 'normal! 10gg3zo')
        self.assertEqual(vim.CMDHISTORY[-2], 'normal! 13gg3zo')
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 16gg3zo')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_other_third_level_half_open_second_level_half_closed(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '6',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '13',
                'foldclosed(16)': '-1',
                })
        self.assertNotEqual(self.showhide.toggle_folding(), None)
        self.assertEqual(len(vim.CMDHISTORY), 4)
        self.assertEqual(vim.CMDHISTORY[-4], 'normal! 6gg3zo')
        self.assertEqual(vim.CMDHISTORY[-3], 'normal! 10gg3zo')
        self.assertEqual(vim.CMDHISTORY[-2], 'normal! 13gg3zo')
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 16gg3zo')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_no_heading_toggle_folding_reverse(self):
        vim.current.window.cursor = (1, 0)
        self.assertEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(vim.EVALHISTORY[-1], 'feedkeys("<Tab>", "n")')
        self.assertEqual(vim.current.window.cursor, (1, 0))

    def test_toggle_folding_first_heading_with_no_children_reverse(self):
        vim.current.buffer[:] = [ i for i in """
* Überschrift 1
Text 1

Bla bla
* Überschrift 2
* Überschrift 3
  asdf sdf
""".split('\n') ]
        vim.EVALRESULTS.update({
                'foldclosed(2)': '2',
                'foldclosed(6)': '-1',
                'foldclosed(7)': '-1',
                })
        vim.current.window.cursor = (2, 0)

        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(vim.CMDHISTORY[-1], '2,5foldopen!')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_close_one_reverse(self):
        vim.current.window.cursor = (13, 0)
        vim.EVALRESULTS.update({
                'foldclosed(13)': '-1',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 13ggzc')
        self.assertEqual(vim.current.window.cursor, (13, 0))

    def test_toggle_folding_open_one_reverse(self):
        vim.current.window.cursor = (10, 0)
        vim.EVALRESULTS.update({
                'foldclosed(10)': '10',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], '10,16foldopen!')
        self.assertEqual(vim.current.window.cursor, (10, 0))

    def test_toggle_folding_close_multiple_all_open_reverse(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '-1',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '-1',
                'foldclosed(16)': '-1',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 2)
        self.assertEqual(vim.CMDHISTORY[-2], 'normal! 13ggzc')
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 16ggzc')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_all_closed_reverse(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '2',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], '2,16foldopen!')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_first_level_open_reverse(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '6',
                'foldclosed(10)': '10',
                'foldclosed(13)': '13',
                'foldclosed(16)': '16',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 2ggzc')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_second_level_half_open_reverse(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '-1',
                'foldclosed(10)': '10',
                'foldclosed(13)': '13',
                'foldclosed(16)': '16',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 6ggzc')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_other_second_level_half_open_reverse(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '6',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '13',
                'foldclosed(16)': '16',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 10ggzc')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_third_level_half_open_reverse(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '-1',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '-1',
                'foldclosed(16)': '16',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 13ggzc')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_other_third_level_half_open_reverse(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '-1',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '13',
                'foldclosed(16)': '-1',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 16ggzc')
        self.assertEqual(vim.current.window.cursor, (2, 0))

    def test_toggle_folding_open_multiple_other_third_level_half_open_second_level_half_closed_reverse(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS.update({
                'foldclosed(2)': '-1',
                'foldclosed(6)': '6',
                'foldclosed(10)': '-1',
                'foldclosed(13)': '13',
                'foldclosed(16)': '-1',
                })
        self.assertNotEqual(self.showhide.toggle_folding(reverse=True), None)
        self.assertEqual(len(vim.CMDHISTORY), 1)
        self.assertEqual(vim.CMDHISTORY[-1], 'normal! 16ggzc')
        self.assertEqual(vim.current.window.cursor, (2, 0))
