
import re

import vim

from orgmode._vim import ORGMODE, echom, realign_tags
from orgmode.keybinding import VIM_PY_CALL, Command, Keybinding, Plug
from orgmode.menu import ActionEntry, Separator, Submenu


class Hyperlinks:
    """ Hyperlinks plugin """

    def __init__(self):
        """ Initialize plugin """
        object.__init__(self)
        # menu entries this plugin should create
        self.menu = ORGMODE.orgmenu + Submenu('Hyperlinks')

        # key bindings for this plugin
        # key bindings are also registered through the menu so only additional
        # bindings should be put in this variable
        self.keybindings = []

        # commands for this plugin
        self.commands = []

    uri_match = re.compile(
        r'^\[{2}(?P<uri>[^][]*)(\]\[(?P<description>[^][]*))?\]{2}')

    @classmethod
    def _get_link(cls, cursor=None):
        """
        Get the link the cursor is on and return it's URI and description

        :cursor: None or (Line, Column)
        :returns: None if no link was found, otherwise {uri:URI,
                description:DESCRIPTION, line:LINE, start:START, end:END}
                or uri and description could be None if not set
        """
        cursor = cursor if cursor else vim.current.window.cursor
        line = vim.current.buffer[cursor[0] - 1]

        # if the cursor is on the last bracket, it's not recognized as a hyperlink
        start = line.rfind('[[', 0, cursor[1])
        if start == -1:
            start = line.rfind('[[', 0, cursor[1] + 2)
        end = line.find(']]', cursor[1])
        if end == -1:
            end = line.find(']]', cursor[1] - 1)

        # extract link
        if start != -1 and end != -1:
            end += 2
            match = Hyperlinks.uri_match.match(line[start:end])

            res = {
                'line': line,
                'start': start,
                'end': end,
                'uri': None,
                'description': None}
            if match:
                res.update(match.groupdict())
            # reverse character escaping(partly done due to matching)
            res['uri'] = res['uri'].replace('\\\\', '\\')
            return res

    @classmethod
    def follow(cls, action='openLink', visual=''):
        """ Follow hyperlink. If called on a regular string UTL determines the
        outcome. Normally a file with that name will be opened.

        :action: "copy" if the link should be copied to clipboard, otherwise
                the link will be opened
        :visual: "visual" if Universal Text Linking should be triggered in
                visual mode

        :returns: URI or None
        """
        if not int(vim.eval('exists(":Utl")')):
            echom('Universal Text Linking plugin not installed, unable to proceed.')
            return

        action = 'copyLink' \
            if (action and action.startswith('copy')) \
            else 'openLink'
        visual = 'visual' if visual and visual.startswith('visual') else ''

        link = Hyperlinks._get_link()

        if link and link['uri'] is not None:
            # call UTL with the URI
            vim.command('Utl %s %s %s' % (action, visual, link['uri']))
            return link['uri']
        else:
            # call UTL and let it decide what to do
            vim.command('Utl %s %s' % (action, visual))

    @classmethod
    @realign_tags
    def insert(cls, uri=None, description=None):
        """ Inserts a hyperlink. If no arguments are provided, an interactive
        query will be started.

        :uri: The URI that will be opened
        :description: An optional description that will be displayed instead of
                the URI

        :returns: (URI, description)
        """
        link = Hyperlinks._get_link()
        if link:
            if uri is None and link['uri'] is not None:
                uri = link['uri']
            if description is None and link['description'] is not None:
                description = link['description']

        if uri is None:
            uri = vim.eval('input("Link: ", "", "file")')
        elif link:
            uri = vim.eval('input("Link: ", "%s", "file")' % link['uri'])
        if uri is None:
            return

        # character escaping
        uri = uri.replace('\\', '\\\\\\\\')
        uri = uri.replace(' ', '\\ ')

        if description is None:
            description = vim.eval('input("Description: ")')
        elif link:
            description = vim.eval(
                'input("Description: ", "%s")' %
                link['description'])
        if description is None:
            return

        cursor = vim.current.window.cursor
        cl = vim.current.buffer[cursor[0] - 1]
        head = cl[:cursor[1] + 1] if not link else cl[:link['start']]
        tail = cl[cursor[1] + 1:] if not link else cl[link['end']:]

        separator = ''
        if description:
            separator = ']['

        if uri or description:
            vim.current.buffer[cursor[0] - 1] = \
                ''.join((head, '[[%s%s%s]]' % (uri, separator, description), tail))
        elif link:
            vim.current.buffer[cursor[0] - 1] = \
                ''.join((head, tail))

    def register(self):
        """
        Registration of plugin. Key bindings and other initialization should be done.
        """
        cmd = Command(
            'OrgHyperlinkFollow',
            '%s ORGMODE.plugins["Hyperlinks"].follow()' % VIM_PY_CALL)
        self.commands.append(cmd)
        self.keybindings.append(
            Keybinding('gl', Plug('OrgHyperlinkFollow', self.commands[-1])))
        self.menu + ActionEntry('&Follow Link', self.keybindings[-1])

        cmd = Command(
            'OrgHyperlinkCopy',
            '%s ORGMODE.plugins["Hyperlinks"].follow(action="copy")' % VIM_PY_CALL)
        self.commands.append(cmd)
        self.keybindings.append(
            Keybinding('gyl', Plug('OrgHyperlinkCopy', self.commands[-1])))
        self.menu + ActionEntry('&Copy Link', self.keybindings[-1])

        cmd = Command(
            'OrgHyperlinkInsert',
            '%s ORGMODE.plugins["Hyperlinks"].insert(<f-args>)' % VIM_PY_CALL,
            arguments='*')
        self.commands.append(cmd)
        self.keybindings.append(
            Keybinding('gil', Plug('OrgHyperlinkInsert', self.commands[-1])))
        self.menu + ActionEntry('&Insert Link', self.keybindings[-1])

        self.menu + Separator()

        # find next link
        cmd = Command(
            'OrgHyperlinkNextLink',
            ":if search('\\[\\{2}\\zs[^][]*\\(\\]\\[[^][]*\\)\\?\\ze\\]\\{2}', 's') == 0 | echo 'No further link found.' | endif")
        self.commands.append(cmd)
        self.keybindings.append(
            Keybinding('gn', Plug('OrgHyperlinkNextLink', self.commands[-1])))
        self.menu + ActionEntry('&Next Link', self.keybindings[-1])

        # find previous link
        cmd = Command(
            'OrgHyperlinkPreviousLink',
            ":if search('\\[\\{2}\\zs[^][]*\\(\\]\\[[^][]*\\)\\?\\ze\\]\\{2}', 'bs') == 0 | echo 'No further link found.' | endif")
        self.commands.append(cmd)
        self.keybindings.append(
            Keybinding('go', Plug('OrgHyperlinkPreviousLink', self.commands[-1])))
        self.menu + ActionEntry('&Previous Link', self.keybindings[-1])

        self.menu + Separator()

        # Descriptive Links
        cmd = Command('OrgHyperlinkDescriptiveLinks', ':setlocal cole=2')
        self.commands.append(cmd)
        self.menu + ActionEntry('&Descriptive Links', self.commands[-1])

        # Literal Links
        cmd = Command('OrgHyperlinkLiteralLinks', ':setlocal cole=0')
        self.commands.append(cmd)
        self.menu + ActionEntry('&Literal Links', self.commands[-1])
