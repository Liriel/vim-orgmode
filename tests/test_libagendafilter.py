# -*- coding: utf-8 -*-


import sys
sys.path.append('../ftplugin')

import unittest
from datetime import date
from datetime import timedelta

from orgmode.liborgmode.headings import Heading
from orgmode.liborgmode.orgdate import OrgDate
from orgmode.liborgmode.agendafilter import contains_active_todo
from orgmode.liborgmode.agendafilter import contains_active_date
from orgmode.liborgmode.orgdate import OrgDateTime
from orgmode.liborgmode.agendafilter import is_within_week
from orgmode.liborgmode.agendafilter import is_within_week_and_active_todo
from orgmode.liborgmode.agendafilter import filter_items

import vim


counter = 0

class AgendaFilterTestCase(unittest.TestCase):
    """Tests all the functionality of the Agenda filter module."""

    def setUp(self):
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
        vim.current.buffer[:] = [i for i in """
* TODO Heading 1
  some text
""".split('\n')]

    def test_contains_active_todo(self):
        heading = Heading(title='Refactor the code', todo='TODO')
        self.assertTrue(contains_active_todo(heading))

        heading = Heading(title='Refactor the code', todo='DONE')
        self.assertFalse(contains_active_todo(heading))

        heading = Heading(title='Refactor the code', todo=None)
        self.assertFalse(contains_active_todo(heading))

    def test_contains_active_date(self):
        heading = Heading(title='Refactor the code', active_date=None)
        self.assertFalse(contains_active_date(heading))

        odate = OrgDate(True, 2011, 11, 1)
        heading = Heading(title='Refactor the code', active_date=odate)
        self.assertTrue(contains_active_date(heading))

    def test_is_within_week_with_orgdate(self):
        # to far in the future
        tmpdate = date.today() + timedelta(days=8)
        odate = OrgDate(True, tmpdate.year, tmpdate.month, tmpdate.day)
        heading = Heading(title='Refactor the code', active_date=odate)
        self.assertFalse(is_within_week(heading))

        # within a week
        tmpdate = date.today() + timedelta(days=5)
        odate = OrgDate(True, tmpdate.year, tmpdate.month, tmpdate.day)
        heading = Heading(title='Refactor the code', active_date=odate)
        self.assertTrue(is_within_week(heading))

        # in the past
        tmpdate = date.today() - timedelta(days=105)
        odate = OrgDate(True, tmpdate.year, tmpdate.month, tmpdate.day)
        heading = Heading(title='Refactor the code', active_date=odate)
        self.assertTrue(is_within_week(heading))

    def test_is_within_week_with_orgdatetime(self):
        # to far in the future
        tmp = date.today() + timedelta(days=1000)
        odate = OrgDateTime(True, tmp.year, tmp.month, tmp.day, 10, 10)
        heading = Heading(title='Refactor the code', active_date=odate)
        self.assertFalse(is_within_week(heading))

        # within a week
        tmpdate = date.today() + timedelta(days=5)
        odate = OrgDateTime(True, tmpdate.year, tmpdate.month, tmpdate.day, 1, 0)
        heading = Heading(title='Refactor the code', active_date=odate)
        self.assertTrue(is_within_week(heading))

        # in the past
        tmpdate = date.today() - timedelta(days=5)
        odate = OrgDateTime(True, tmpdate.year, tmpdate.month, tmpdate.day, 1, 0)
        heading = Heading(title='Refactor the code', active_date=odate)
        self.assertTrue(is_within_week(heading))

    def test_filter_items(self):
        # only headings with date and todo should be returned
        vim.EVALRESULTS['g:org_todo_keywords'] = \
                ['TODO', 'STARTED', '|', 'DONE']
        tmpdate = date.today()
        odate = OrgDate(True, tmpdate.year, tmpdate.month, tmpdate.day)
        tmp_head = Heading(title='Refactor the code', todo='TODO', active_date=odate)
        tmp_head_01 = Heading(title='Refactor the code', todo='STARTED', active_date=odate)
        # TODO add more tests
        headings = [tmp_head, tmp_head_01]
        filtered = list(filter_items(headings,
                [contains_active_date, contains_active_todo]))

        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered, headings)

        # try a longer list
        headings = headings * 3
        filtered = list(filter_items(headings,
                [contains_active_date, contains_active_todo]))

        self.assertEqual(len(filtered), 6)
        self.assertEqual(filtered, headings)

        # date does not contain all needed fields thus gets ignored
        tmpdate = date.today()
        odate = OrgDate(True, tmpdate.year, tmpdate.month, tmpdate.day)
        tmp_head = Heading(title='Refactor the code', active_date=odate)
        headings = [tmp_head]
        filtered = list(filter_items(headings, [contains_active_date,
                contains_active_todo]))
        self.assertEqual([], filtered)

    def test_filter_items_with_some_todos_and_dates(self):
        """
        Only the headings with todo and dates should be returned.
        """
        tmp = ["* TODO OrgMode Demo und Tests"
                "<2011-08-22 Mon>"]
        headings = [Heading.parse_heading_from_data(tmp, ['TODO'])]
        filtered = list(filter_items(headings,
                               [is_within_week_and_active_todo]))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(headings, filtered)

        tmp = [Heading.parse_heading_from_data(["** DONE something <2011-08-10 Wed>"], ['TODO']),
                Heading.parse_heading_from_data(["*** TODO rsitenaoritns more <2011-08-25 Thu>"], ['TODO']),
                Heading.parse_heading_from_data(["*** DONE some more <2011-08-25 Thu>"], ['TODO']),
                Heading.parse_heading_from_data(["*** TODO some more <2011-08-25 Thu>"], ['TODO']),
                Heading.parse_heading_from_data(["** DONE something2 <2011-08-10 Wed>"], ['TODO'])
        ]
        for h in tmp:
            headings.append(h)

        filtered = list(filter_items(headings,
                               [is_within_week_and_active_todo]))
        self.assertEqual(len(filtered), 3)
        self.assertEqual(filtered, [headings[0], headings[2], headings[4]])

    def test_agenda_sorting_key_undated_heading_sorts_last(self):
        """
        Undated headings (e.g. a plain TODO in the todo view) must be sortable
        together with dated ones instead of raising TypeError.
        """
        from orgmode.liborgmode.agenda import agenda_sorting_key
        undated = Heading.parse_heading_from_data(["* TODO undated"], ['TODO'])
        d1 = Heading.parse_heading_from_data(["* TODO a <2011-08-25 Thu>"], ['TODO'])
        d2 = Heading.parse_heading_from_data(["* TODO b <2011-08-20 Sat 10:00>"], ['TODO'])
        result = sorted([undated, d1, d2], key=agenda_sorting_key)
        self.assertEqual(result, [d2, d1, undated])


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(AgendaFilterTestCase)
