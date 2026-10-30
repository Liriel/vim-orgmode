import operator
import re
from datetime import date, datetime, timedelta

import vim

from orgmode._vim import ORGMODE, echom, get_user_input, insert_at_cursor
from orgmode.keybinding import VIM_PY_CALL
from orgmode.menu import ActionEntry, Submenu, add_cmd_mapping_menu


class Date:
    """
    Handles all date and timestamp related tasks.

    TODO: extend functionality (calendar, repetitions, ranges). See
            http://orgmode.org/guide/Dates-and-Times.html#Dates-and-Times
    """

    date_regex = r"\d\d\d\d-\d\d-\d\d"
    datetime_regex = r"[A-Z]\w\w \d\d\d\d-\d\d-\d\d \d\d:\d\d>"

    month_mapping = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11,
        'dec': 12}

    def __init__(self):
        """ Initialize plugin """
        object.__init__(self)
        # menu entries this plugin should create
        self.menu = ORGMODE.orgmenu + Submenu('Dates and Scheduling')

        # key bindings for this plugin
        # key bindings are also registered through the menu so only additional
        # bindings should be put in this variable
        self.keybindings = []

        # commands for this plugin
        self.commands = []

        # set speeddating format that is compatible with orgmode
        try:
            if int(vim.eval('exists(":SpeedDatingFormat")')) == 2:
                vim.command(':1SpeedDatingFormat %Y-%m-%d %a')
                vim.command(':1SpeedDatingFormat %Y-%m-%d %a %H:%M')
            else:
                echom('Speeddating plugin not installed. Please install it.')
        except Exception:
            echom('Speeddating plugin not installed. Please install it.')

    @classmethod
    def _modify_time(cls, startdate, modifier):
        """Modify the given startdate according to modifier. Return the new
        date or datetime.

        See http://orgmode.org/manual/The-date_002ftime-prompt.html
        """
        if modifier is None or modifier == '' or modifier == '.':
            return startdate

        # rm crap from modifier
        modifier = modifier.strip()

        ops = {'-': operator.sub, '+': operator.add}

        # check real date
        date_regex = r"(\d\d\d\d)-(\d\d)-(\d\d)"
        match = re.search(date_regex, modifier)
        if match:
            year, month, day = match.groups()
            newdate = date(int(year), int(month), int(day))

        # check abbreviated date, separated with '-'
        date_regex = "(\\d{1,2})-(\\d+)-(\\d+)"
        match = re.search(date_regex, modifier)
        if match:
            year, month, day = match.groups()
            newdate = date(2000 + int(year), int(month), int(day))

        # check abbreviated date, separated with '/'
        # month/day
        date_regex = "(\\d{1,2})/(\\d{1,2})"
        match = re.search(date_regex, modifier)
        if match:
            month, day = match.groups()
            newdate = date(startdate.year, int(month), int(day))
            # date should be always in the future
            if newdate < startdate:
                newdate = date(startdate.year + 1, int(month), int(day))

        # check full date, separated with 'space'
        # month day year
        # 'sep 12 9' --> 2009 9 12
        date_regex = "(\\w\\w\\w) (\\d{1,2}) (\\d{1,2})"
        match = re.search(date_regex, modifier)
        if match:
            gr = match.groups()
            day = int(gr[1])
            month = int(cls.month_mapping[gr[0]])
            year = 2000 + int(gr[2])
            newdate = date(year, int(month), int(day))

        # check days as integers
        date_regex = "^(\\d{1,2})$"
        match = re.search(date_regex, modifier)
        if match:
            newday, = match.groups()
            newday = int(newday)
            if newday > startdate.day:
                newdate = date(startdate.year, startdate.month, newday)
            else:
                # TODO: DIRTY, fix this
                #       this does NOT cover all edge cases
                newdate = startdate + timedelta(days=28)
                newdate = date(newdate.year, newdate.month, newday)

        # check for full days: Mon, Tue, Wed, Thu, Fri, Sat, Sun
        modifier_lc = modifier.lower()
        match = re.search('mon|tue|wed|thu|fri|sat|sun', modifier_lc)
        if match:
            weekday_mapping = {
                'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
                'fri': 4, 'sat': 5, 'sun': 6}
            diff = (weekday_mapping[modifier_lc] - startdate.weekday()) % 7
            # use next weeks weekday if current weekday is the same as modifier
            if diff == 0:
                diff = 7
            newdate = startdate + timedelta(days=diff)

        # check for days modifier with appended d
        match = re.search('^(\\+|-)(\\d*)d', modifier)
        if match:
            op, days = match.groups()
            newdate = ops[op](startdate, timedelta(days=int(days)))

        # check for days modifier without appended d
        match = re.search('^(\\+|-)(\\d*) |^(\\+|-)(\\d*)$', modifier)
        if match:
            groups = match.groups()
            try:
                op = groups[0]
                days = int(groups[1])
            except Exception:
                op = groups[2]
                days = int(groups[3])
            newdate = ops[op](startdate, timedelta(days=days))

        # check for week modifier
        match = re.search('^(\\+|-)(\\d+)w', modifier)
        if match:
            op, weeks = match.groups()
            newdate = ops[op](startdate, timedelta(weeks=int(weeks)))

        # check for month modifier
        match = re.search('^(\\+|-)(\\d+)m', modifier)
        if match:
            op, months = match.groups()
            newdate = date(startdate.year, ops[op](startdate.month, int(months)),
                    startdate.day)

        # check for year modifier
        match = re.search('^(\\+|-)(\\d*)y', modifier)
        if match:
            op, years = match.groups()
            newdate = date(ops[op](startdate.year, int(years)), startdate.month,
                    startdate.day)

        # check for month day
        match = re.search(
            '(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (\\d{1,2})',
            modifier.lower())
        if match:
            month = cls.month_mapping[match.groups()[0]]
            day = int(match.groups()[1])
            newdate = date(startdate.year, int(month), int(day))
            # date should be always in the future
            if newdate < startdate:
                newdate = date(startdate.year + 1, int(month), int(day))

        # check abbreviated date, separated with '/'
        # month/day/year
        date_regex = "(\\d{1,2})/(\\d+)/(\\d+)"
        match = re.search(date_regex, modifier)
        if match:
            month, day, year = match.groups()
            newdate = date(2000 + int(year), int(month), int(day))

        # check for month day year
        # sep 12 2011
        match = re.search(
            '(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (\\d{1,2}) (\\d{1,4})',
            modifier.lower())
        if match:
            month = int(cls.month_mapping[match.groups()[0]])
            day = int(match.groups()[1])
            if len(match.groups()[2]) < 4:
                year = 2000 + int(match.groups()[2])
            else:
                year = int(match.groups()[2])
            newdate = date(year, month, day)

        # check for time: HH:MM
        # '12:45' --> datetime(2006, 06, 13, 12, 45))
        match = re.search('(\\d{1,2}):(\\d\\d)$', modifier)
        if match:
            try:
                startdate = newdate
            except Exception:
                pass
            return datetime(
                startdate.year, startdate.month, startdate.day,
                int(match.groups()[0]), int(match.groups()[1]))

        try:
            return newdate
        except Exception:
            return startdate

    @classmethod
    def insert_timestamp(cls, active=True):
        """
        Insert a timestamp at the cursor position.

        TODO: show fancy calendar to pick the date from.
        TODO: add all modifier of orgmode.
        """
        today = date.today()
        msg = ''.join([
            'Inserting ',
            str(today.strftime('%Y-%m-%d %a')),
            ' | Modify date'])
        modifier = get_user_input(msg)

        # abort if the user canceled the input prompt
        if modifier is None:
            return

        newdate = cls._modify_time(today, modifier)

        # format
        if isinstance(newdate, datetime):
            newdate = newdate.strftime(
                '%Y-%m-%d %a %H:%M')
        else:
            newdate = newdate.strftime(
                '%Y-%m-%d %a')
        timestamp = '<%s>' % newdate if active else '[%s]' % newdate

        insert_at_cursor(timestamp)

    @classmethod
    def insert_timestamp_with_calendar(cls, active=True):
        """
        Insert a timestamp at the cursor position.
        Show fancy calendar to pick the date from.

        TODO: add all modifier of orgmode.
        """
        if int(vim.eval('exists(":CalendarH")')) != 2:
            vim.command("echo 'Please install plugin Calendar to enable this function'")
            return
        vim.command("CalendarH")
        # backup calendar_action
        calendar_action = vim.eval("g:calendar_action")
        vim.command("let g:org_calendar_action_backup = '" + calendar_action + "'")
        vim.command("let g:calendar_action = 'CalendarAction'")

        timestamp_template = '<%s>' if active else '[%s]'
        # timestamp template
        vim.command("let g:org_timestamp_template = '" + timestamp_template + "'")

    def register(self):
        """
        Registration of the plugin.

        Key bindings and other initialization should be done here.
        """
        add_cmd_mapping_menu(
            self,
            name='OrgDateInsertTimestampActiveCmdLine',
            key_mapping='<localleader>sa',
            function='%s ORGMODE.plugins["Date"].insert_timestamp()' % VIM_PY_CALL,
            menu_desrc='Timest&amp'
        )
        add_cmd_mapping_menu(
            self,
            name='OrgDateInsertTimestampInactiveCmdLine',
            key_mapping='<localleader>si',
            function='%s ORGMODE.plugins["Date"].insert_timestamp(False)' % VIM_PY_CALL,
            menu_desrc='Timestamp (&inactive)'
        )
        add_cmd_mapping_menu(
            self,
            name='OrgDateInsertTimestampActiveWithCalendar',
            key_mapping='<localleader>pa',
            function='%s ORGMODE.plugins["Date"].insert_timestamp_with_calendar()' % VIM_PY_CALL,
            menu_desrc='Timestamp with Calendar'
        )
        add_cmd_mapping_menu(
            self,
            name='OrgDateInsertTimestampInactiveWithCalendar',
            key_mapping='<localleader>pi',
            function='%s ORGMODE.plugins["Date"].insert_timestamp_with_calendar(False)' % VIM_PY_CALL,
            menu_desrc='Timestamp with Calendar(inactive)'
        )

        submenu = self.menu + Submenu('Change &Date')
        submenu + ActionEntry('Day &Earlier', '<C-x>', '<C-x>')
        submenu + ActionEntry('Day &Later', '<C-a>', '<C-a>')
