# -*- coding: utf-8 -*-

"""
    Agenda
    ~~~~~~~~~~~~~~~~~~

    The agenda is one of the main concepts of orgmode. It allows to
    collect TODO items from multiple org documents in an agenda view.

    Features:
    * filtering
    * sorting
"""

from datetime import datetime

from orgmode.liborgmode.agendafilter import filter_items
from orgmode.liborgmode.agendafilter import is_within_week_and_active_todo
from orgmode.liborgmode.agendafilter import contains_active_todo
from orgmode.liborgmode.agendafilter import contains_active_date
from orgmode.liborgmode.orgdate import orgdate_to_datetime

def agenda_sorting_key(heading):
    # headings without an active date (e.g. plain TODOs) sort after all dated
    # ones; a bare None cannot be compared with a datetime
    active = orgdate_to_datetime(heading.active_date)
    if active is None:
        return (1, datetime.max)
    return (0, active)

class AgendaManager(object):
    """Simple parsing of Documents to create an agenda."""
    # TODO Move filters in this file, they do the same thing

    def __init__(self):
        super(AgendaManager, self).__init__()

    def get_todo(self, documents):
        """
        Get the todo agenda for the given documents (list of document).
        """
        filtered = []
        for document in iter(documents):
            # filter and return headings
            filtered.extend(filter_items(document.all_headings(),
                                [contains_active_todo]))
        return sorted(filtered, key=agenda_sorting_key)

    def get_next_week_and_active_todo(self, documents):
        """
        Get the agenda for next week for the given documents (list of
        document).
        """
        filtered = []
        for document in iter(documents):
            # filter and return headings
            filtered.extend(filter_items(document.all_headings(),
                                [is_within_week_and_active_todo]))
        return sorted(filtered, key=agenda_sorting_key)

    def get_timestamped_items(self, documents):
        """
        Get all time-stamped items in a time-sorted way for the given
        documents (list of document).
        """
        filtered = []
        for document in iter(documents):
            # filter and return headings
            filtered.extend(filter_items(document.all_headings(),
                                [contains_active_date]))
        return sorted(filtered, key=agenda_sorting_key)
