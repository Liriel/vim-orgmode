# -*- coding: utf-8 -*-

import unittest
import sys
sys.path.append('../ftplugin')

from orgmode.liborgmode.headings import Heading
from orgmode.liborgmode.orgdate import OrgDate
from orgmode.liborgmode.orgdate import OrgDateTime


class TestHeadingRecognizeDatesInHeading(unittest.TestCase):

    def setUp(self):
        self.allowed_todo_states = ["TODO"]

        tmp = ["* This heading is earlier  <2011-08-24 Wed>"]
        self.h1 = Heading.parse_heading_from_data(tmp, self.allowed_todo_states)

        tmp = ["* This heading is later <2011-08-25 Thu>"]
        self.h2 = Heading.parse_heading_from_data(tmp, self.allowed_todo_states)

        tmp = ["* This heading is later <2011-08-25 Thu 10:20>"]
        self.h2_datetime = Heading.parse_heading_from_data(tmp, self.allowed_todo_states)

        tmp = ["* This heading is later <2011-08-26 Fri 10:20>"]
        self.h3 = Heading.parse_heading_from_data(tmp, self.allowed_todo_states)

        tmp = ["* This heading has no date and should be later than the rest"]
        self.h_no_date = Heading.parse_heading_from_data(tmp,
                self.allowed_todo_states)

    def test_heading_parsing_no_date(self):
        """""
        'text' doesn't contain any valid date.
        """
        text = ["* TODO This is a test :hallo:"]
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        self.assertEqual(None, h.active_date)

        text = ["* TODO This is a test <2011-08-25>"]
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        self.assertEqual(None, h.active_date)

        text = ["* TODO This is a test <2011-08-25 Wednesday>"]
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        self.assertEqual(None, h.active_date)

        text = ["* TODO This is a test <20110825>"]
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        self.assertEqual(None, h.active_date)

    def test_heading_parsing_with_date(self):
        """""
        'text' does contain valid dates.
        """
        # orgdate
        text = ["* TODO This is a test <2011-08-24 Wed> :hallo:"]
        odate = OrgDate(True, 2011, 8, 24)
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        self.assertEqual(odate, h.active_date)

        # orgdatetime
        text = ["* TODO This is a test <2011-08-25 Thu 10:10> :hallo:"]
        odate = OrgDateTime(True, 2011, 8, 25, 10, 10)
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        self.assertEqual(odate, h.active_date)

    def test_heading_parsing_with_date_and_body(self):
        """""
        'text' contains valid dates (in the body).
        """
        # orgdatetime
        text = ["* TODO This is a test <2011-08-25 Thu 10:10> :hallo:",
                "some body text",
                "some body text"]
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        self.assertTrue(isinstance(h.active_date, OrgDateTime))
        self.assertEqual("<2011-08-25 Thu 10:10>", str(h.active_date))

        text = ["* TODO This is a test  :hallo:",
                "some body text",
                "some body text<2011-08-25 Thu 10:10>"]
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        self.assertTrue(isinstance(h.active_date, OrgDateTime))
        self.assertEqual("<2011-08-25 Thu 10:10>", str(h.active_date))

        text = ["* TODO This is a test  :hallo:",
                "some body text <2011-08-24 Wed>",
                "some body text<2011-08-25 Thu 10:10>"]
        h = Heading.parse_heading_from_data(text, self.allowed_todo_states)
        odate = OrgDate(True, 2011, 8, 24)
        self.assertEqual(odate, h.active_date)

    def test_less_than_for_dates_in_heading(self):
        self.assertTrue(self.h1 < self.h2)
        self.assertTrue(self.h1 < self.h3)
        self.assertTrue(self.h1 < self.h_no_date)
        self.assertTrue(self.h2 < self.h_no_date)
        self.assertTrue(self.h2 < self.h3)
        self.assertTrue(self.h3 < self.h_no_date)

        self.assertFalse(self.h2 < self.h1)
        self.assertFalse(self.h3 < self.h2)

    def test_less_equal_for_dates_in_heading(self):
        self.assertTrue(self.h1 <= self.h2)
        self.assertTrue(self.h1 <= self.h_no_date)
        self.assertTrue(self.h2 <= self.h_no_date)
        self.assertTrue(self.h2 <= self.h2_datetime)
        self.assertTrue(self.h2 <= self.h3)

    def test_greate_than_for_dates_in_heading(self):
        self.assertTrue(self.h2 > self.h1)
        self.assertTrue(self.h_no_date > self.h1)
        self.assertTrue(self.h_no_date > self.h2)

        self.assertFalse(self.h2 > self.h2_datetime)

    def test_greate_equal_for_dates_in_heading(self):
        self.assertTrue(self.h2 >= self.h1)
        self.assertTrue(self.h_no_date >= self.h1)
        self.assertTrue(self.h_no_date >= self.h2)
        self.assertTrue(self.h2 >= self.h2_datetime)

    def test_comparing_date_with_datetime_returns_bool(self):
        # Regression: comparisons used to return None for OrgDate vs
        # OrgDateTime because the TypeError was swallowed
        for op in (lambda a, b: a < b, lambda a, b: a <= b,
                lambda a, b: a > b, lambda a, b: a >= b):
            for a in (self.h1, self.h2, self.h2_datetime, self.h_no_date):
                for b in (self.h1, self.h2, self.h2_datetime, self.h_no_date):
                    self.assertTrue(op(a, b) in (True, False))
        self.assertTrue(self.h2_datetime < self.h3)
        self.assertTrue(self.h1 < self.h2_datetime)
        self.assertFalse(self.h2_datetime < self.h1)

    def test_headings_keep_identity_equality(self):
        copy = self.h1.copy()
        self.assertFalse(self.h1 == copy)
        self.assertTrue(self.h1 in [self.h1])
        self.assertFalse(copy in [self.h1])

    def test_sorting_of_headings(self):
        """Headings should be sortable."""
        self.assertEqual([self.h1, self.h2], sorted([self.h2, self.h1]))

        self.assertEqual([self.h1, self.h2_datetime],
                sorted([self.h2_datetime, self.h1]))

        self.assertEqual([self.h2_datetime, self.h2],
                sorted([self.h2_datetime, self.h2]))

        self.assertEqual([self.h1, self.h2], sorted([self.h1, self.h2]))

        self.assertEqual([self.h1, self.h_no_date],
                sorted([self.h1, self.h_no_date]))

        self.assertEqual([self.h1, self.h_no_date],
                sorted([self.h_no_date, self.h1]))

        self.assertEqual([self.h1, self.h2, self.h_no_date],
                sorted([self.h2, self.h_no_date, self.h1]))

        self.assertEqual(
                [self.h1, self.h2_datetime, self.h2, self.h3, self.h_no_date],
                sorted([self.h2_datetime, self.h3, self.h2, self.h_no_date, self.h1]))


class TestHeadingChildrenSlicing(unittest.TestCase):
    def test_slicing_children_does_not_detach_them(self):
        parent = Heading(level=1, title='parent')
        child1 = Heading(level=2, title='child1')
        child2 = Heading(level=2, title='child2')
        parent.children.append(child1)
        parent.children.append(child2)
        child1._orig_start = 3
        child2._orig_start = 5

        for sliced in (parent.children[:], parent.children[::-1],
                parent.children[0:1]):
            self.assertEqual(type(sliced), list)

        self.assertEqual(child1._orig_start, 3)
        self.assertEqual(child2._orig_start, 5)
        self.assertTrue(child1.parent is parent)
        self.assertTrue(child2.parent is parent)
        self.assertTrue(child1.next_sibling is child2)
        self.assertTrue(child2.previous_sibling is child1)


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            TestHeadingRecognizeDatesInHeading))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            TestHeadingChildrenSlicing))
    return suite
