#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
sys.path.append(u'../ftplugin')

import vim

from orgmode._vim import indent_orgmode, fold_orgmode, ORGMODE


ORGMODE.debug = True

START = True
END = False

counter = 0
class TagsPropertiesTestCase(unittest.TestCase):
    def setUp(self):
        global counter
        counter += 1
        vim.CMDHISTORY = []
        vim.CMDRESULTS = {}
        vim.EVALHISTORY = []
        vim.EVALRESULTS = {
                # no org_todo_keywords for b
                u'exists("b:org_todo_keywords")': '0',
                # global values for org_todo_keywords
                u'exists("g:org_todo_keywords")': '1',
                u'g:org_todo_keywords': [u'TODO', u'|', u'DONE'],
                u'&ts': u'6',
                u'exists("b:org_tag_column")': u'0',
                u'exists("g:org_tag_column")': u'0',
                u'exists("g:org_debug")': u'0',
                u'exists("b:org_debug")': u'0',
                u'exists("*repeat#set()")': u'0',
                u'b:changedtick': (u'%d' % counter),
                u"v:count": u'0'}
        if not u'TagsProperties' in ORGMODE.plugins:
            ORGMODE.register_plugin(u'TagsProperties')
        self.tagsproperties = ORGMODE.plugins[u'TagsProperties']
        vim.current.buffer[:] = [ i for i in u"""
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
""".split(u'\n') ]

    def test_new_property(self):
        u""" TODO: Docstring for test_new_property

        :returns: TODO
        """
        pass

    def test_set_tags(self):
        # set first tag
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u':hello:'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:')

        # set second tag
        vim.EVALRESULTS[u'input("Tags: ", ":hello:", "customlist,Org_complete_tags")'] = u':hello:world:'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')

    def test_parse_tags_no_colons_single_tag(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u'hello'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:')

    def test_parse_tags_no_colons_multiple_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u'hello:world'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')

    def test_parse_tags_single_colon_left_single_tag(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u':hello'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:')

    def test_parse_tags_single_colon_left_multiple_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u':hello:world'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')

    def test_parse_tags_single_colon_right_single_tag(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u'hello:'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:')

    def test_parse_tags_single_colon_right_multiple_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u'hello:world:'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')

    def test_filter_empty_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u'::hello::'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:')

    def test_delete_tags(self):
        # set up
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u':hello:world:'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')

        # delete second of two tags
        vim.EVALRESULTS[u'input("Tags: ", ":hello:world:", "customlist,Org_complete_tags")'] = u':hello:'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:')

        # delete last tag
        vim.EVALRESULTS[u'input("Tags: ", ":hello:", "customlist,Org_complete_tags")'] = u''
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1')

    def test_realign_tags_noop(self):
        vim.current.window.cursor = (2, 0)
        self.tagsproperties.realign_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1')

    def test_realign_tags_remove_spaces(self):
        # remove spaces in multiple locations
        vim.current.buffer[1] = u'*  Überschrift 1 '
        vim.current.window.cursor = (2, 0)
        self.tagsproperties.realign_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1')

        # remove tabs and spaces in multiple locations
        vim.current.buffer[1] = u'*\t  \tÜberschrift 1 \t'
        vim.current.window.cursor = (2, 0)
        self.tagsproperties.realign_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1')

    def test_realign_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS[u'input("Tags: ", "", "customlist,Org_complete_tags")'] = u':hello:world:'
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')

        d = ORGMODE.get_document()
        heading = d.find_current_heading()
        self.assertEqual(str(heading), u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')
        self.tagsproperties.realign_tags()
        heading = d.find_current_heading()
        self.assertEqual(str(heading), u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')
        self.assertEqual(vim.current.buffer[1], u'* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:')

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TagsPropertiesTestCase)
