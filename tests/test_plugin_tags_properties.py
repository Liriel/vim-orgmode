#!/usr/bin/env python

import unittest

import vim

from orgmode._vim import ORGMODE

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
            'exists("b:org_todo_keywords")': "0",
            # global values for org_todo_keywords
            'exists("g:org_todo_keywords")': "1",
            "g:org_todo_keywords": ["TODO", "|", "DONE"],
            "&ts": "6",
            'exists("b:org_tag_column")': "0",
            'exists("g:org_tag_column")': "0",
            'exists("g:org_debug")': "0",
            'exists("b:org_debug")': "0",
            'exists("*repeat#set()")': "0",
            "b:changedtick": ("%d" % counter),
            "v:count": "0",
        }
        if "TagsProperties" not in ORGMODE.plugins:
            ORGMODE.register_plugin("TagsProperties")
        self.tagsproperties = ORGMODE.plugins["TagsProperties"]
        vim.current.buffer[:] = [
            i
            for i in """
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
""".split("\n")
        ]

    def test_new_property(self):
        """TODO: Docstring for test_new_property

        :returns: TODO
        """
        pass

    def test_set_tags(self):
        # set first tag
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            ":hello:"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:"
        )

        # set second tag
        vim.EVALRESULTS[
            'input("Tags: ", ":hello:", "customlist,Org_complete_tags")'
        ] = ":hello:world:"
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )

    def test_parse_tags_no_colons_single_tag(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = "hello"
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:"
        )

    def test_parse_tags_no_colons_multiple_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            "hello:world"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )

    def test_parse_tags_single_colon_left_single_tag(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            ":hello"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:"
        )

    def test_parse_tags_single_colon_left_multiple_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            ":hello:world"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )

    def test_parse_tags_single_colon_right_single_tag(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            "hello:"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:"
        )

    def test_parse_tags_single_colon_right_multiple_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            "hello:world:"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )

    def test_filter_empty_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            "::hello::"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:"
        )

    def test_delete_tags(self):
        # set up
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            ":hello:world:"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )

        # delete second of two tags
        vim.EVALRESULTS[
            'input("Tags: ", ":hello:world:", "customlist,Org_complete_tags")'
        ] = ":hello:"
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t\t    :hello:"
        )

        # delete last tag
        vim.EVALRESULTS[
            'input("Tags: ", ":hello:", "customlist,Org_complete_tags")'
        ] = ""
        self.tagsproperties.set_tags()
        self.assertEqual(vim.current.buffer[1], "* Überschrift 1")

    def test_realign_tags_noop(self):
        vim.current.window.cursor = (2, 0)
        self.tagsproperties.realign_tags()
        self.assertEqual(vim.current.buffer[1], "* Überschrift 1")

    def test_realign_tags_remove_spaces(self):
        # remove spaces in multiple locations
        vim.current.buffer[1] = "*  Überschrift 1 "
        vim.current.window.cursor = (2, 0)
        self.tagsproperties.realign_tags()
        self.assertEqual(vim.current.buffer[1], "* Überschrift 1")

        # remove tabs and spaces in multiple locations
        vim.current.buffer[1] = "*\t  \tÜberschrift 1 \t"
        vim.current.window.cursor = (2, 0)
        self.tagsproperties.realign_tags()
        self.assertEqual(vim.current.buffer[1], "* Überschrift 1")

    def test_realign_tags(self):
        vim.current.window.cursor = (2, 0)
        vim.EVALRESULTS['input("Tags: ", "", "customlist,Org_complete_tags")'] = (
            ":hello:world:"
        )
        self.tagsproperties.set_tags()
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )

        d = ORGMODE.get_document()
        heading = d.find_current_heading()
        self.assertEqual(
            str(heading), "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )
        self.tagsproperties.realign_tags()
        heading = d.find_current_heading()
        self.assertEqual(
            str(heading), "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )
        self.assertEqual(
            vim.current.buffer[1], "* Überschrift 1\t\t\t\t\t\t\t\t    :hello:world:"
        )
