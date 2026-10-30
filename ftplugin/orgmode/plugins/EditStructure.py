# -*- coding: utf-8 -*-

import vim

from orgmode._vim import ORGMODE, apply_count, repeat, realign_tags
from orgmode import settings
from orgmode.exceptions import HeadingDomError
from orgmode.keybinding import Keybinding, Plug, MODE_INSERT, MODE_NORMAL, VIM_PY_CALL
from orgmode.menu import Submenu, Separator, ActionEntry
from orgmode.liborgmode.base import Direction
from orgmode.liborgmode.headings import Heading



class EditStructure(object):
    """ EditStructure plugin """

    def __init__(self):
        """ Initialize plugin """
        object.__init__(self)
        # menu entries this plugin should create
        self.menu = ORGMODE.orgmenu + Submenu('&Edit Structure')

        # key bindings for this plugin
        # key bindings are also registered through the menu so only additional
        # bindings should be put in this variable
        self.keybindings = []

    @classmethod
    def new_heading(cls, below=None, insert_mode=False, end_of_last_child=False):
        """
        :below:                True, insert heading below current heading, False,
                            insert heading above current heading, None, special
                            behavior for insert mode, use the current text as
                            heading
        :insert_mode:        True, if action is performed in insert mode
        :end_of_last_child:    True, insert heading at the end of last child,
                            otherwise the newly created heading will "take
                            over" the current heading's children
        """
        d = ORGMODE.get_document()
        current_heading = d.current_heading()
        cursor = vim.current.window.cursor[:]
        if not current_heading:
            # the user is in meta data region
            pos = cursor[0] - 1
            heading = Heading(title=d.meta_information[pos], body=d.meta_information[pos + 1:])
            d.headings.insert(0, heading)
            del d.meta_information[pos:]
            d.write()
            vim.command('exe "normal %dgg"|startinsert!' % (heading.start_vim, ))
            return heading

        # check for plain list(checkbox)
        current_heading.init_checkboxes()
        c = current_heading.current_checkbox()
        if c is not None:
            ORGMODE.plugins["EditCheckbox"].new_checkbox(below, not c.status)
            return

        heading = Heading(level=current_heading.level)

        # it's weird but this is the behavior of original orgmode
        if below is None:
            below = cursor[1] != 0 or end_of_last_child

        # insert newly created heading
        l = current_heading.get_parent_list()
        idx = current_heading.get_index_in_parent_list()
        if l is not None and idx is not None:
            l.insert(idx + (1 if below else 0), heading)
        else:
            raise HeadingDomError('Current heading is not properly linked in DOM')

        if below and not end_of_last_child:
            # append heading at the end of current heading and also take
            # over the children of current heading
            for child in current_heading.children:
                heading.children.append(child, taint=False)
            current_heading.children.remove_slice(
                0, len(current_heading.children),
                taint=False)

        # if cursor is currently on a heading, insert parts of it into the
        # newly created heading
        if insert_mode and cursor[1] != 0 and cursor[0] == current_heading.start_vim:
            offset = cursor[1] - current_heading.level - 1 - (
                len(current_heading.todo) + 1 if current_heading.todo else 0)
            if offset < 0:
                offset = 0
            if int(settings.get('org_improve_split_heading', '1')) and \
                offset > 0 and len(current_heading.title) == offset + 1 \
                and current_heading.title[offset - 1] not in (' ', '\t'):
                offset += 1
            heading.title = current_heading.title[offset:]
            current_heading.title = current_heading.title[:offset]
            heading.body = current_heading.body[:]
            current_heading.body = []

        d.write()
        # do not start insert upon adding new headings, unless already in insert mode. Issue #211
        if int(settings.get('org_prefer_insert_mode', '1')) or insert_mode:
            vim.command('exe "normal %dgg"|startinsert!' % (heading.start_vim, ))
        else:
            vim.command('exe "normal %dgg$"' % (heading.start_vim, ))

        # return newly created heading
        return heading

    @classmethod
    def _append_heading(cls, heading, parent):
        if heading.level <= parent.level:
            raise ValueError('Heading level not is lower than parent level: %d ! > %d' % (heading.level, parent.level))

        if parent.children and parent.children[-1].level < heading.level:
            cls._append_heading(heading, parent.children[-1])
        else:
            parent.children.append(heading, taint=False)

    @classmethod
    def _change_heading_level(cls, level, including_children=True, on_heading=False, insert_mode=False):
        """
        Change level of heading realtively with or without including children.

        :level:                    the number of levels to promote/demote heading
        :including_children:    True if should should be included in promoting/demoting
        :on_heading:            True if promoting/demoting should only happen when the cursor is on the heading
        :insert_mode:            True if vim is in insert mode
        """
        # TODO : current promote and demote works for only headings. Since
        #          checkboxes also have tree structure. We should think of
        #          expanding the functionality of promoting and demoting to
        #          checkboxes as well
        d = ORGMODE.get_document()
        current_heading = d.current_heading()
        if not current_heading or on_heading and current_heading.start_vim != vim.current.window.cursor[0]:
            # TODO figure out the actually pressed keybinding and feed these
            # keys instead of making keys up like this
            if level > 0:
                if insert_mode:
                    vim.eval('feedkeys("\\<C-t>", "n")')
                elif including_children:
                    vim.eval('feedkeys(">]]", "n")')
                elif on_heading:
                    vim.eval('feedkeys(">>", "n")')
                else:
                    vim.eval('feedkeys(">}", "n")')
            else:
                if insert_mode:
                    vim.eval('feedkeys("\\<C-d>", "n")')
                elif including_children:
                    vim.eval('feedkeys("<]]", "n")')
                elif on_heading:
                    vim.eval('feedkeys("<<", "n")')
                else:
                    vim.eval('feedkeys("<}", "n")')
            # return True because otherwise apply_count will not work
            return True

        # don't allow demotion below level 1
        if current_heading.level == 1 and level < 1:
            return False

        # reduce level of demotion to a minimum heading level of 1
        if (current_heading.level + level) < 1:
            level = 1

        def indent(heading, ic):
            if not heading:
                return
            heading.level += level

            if ic:
                for child in heading.children:
                    indent(child, ic)

        # save cursor position
        c = vim.current.window.cursor[:]

        # indent the promoted/demoted heading
        indent_end_vim = current_heading.end_of_last_child_vim if including_children else current_heading.end_vim
        indent(current_heading, including_children)

        # when changing the level of a heading, its position in the DOM
        # needs to be updated. It's likely that the heading gets a new
        # parent and new children when demoted or promoted

        # find new parent
        p = current_heading.parent
        pl = current_heading.get_parent_list()
        ps = current_heading.previous_sibling
        nhl = current_heading.level

        if level > 0:
            # demotion
            # subheading or top level heading
            if ps and nhl > ps.level:
                pl.remove(current_heading, taint=False)
                # find heading that is the new parent heading
                oh = ps
                h = ps
                while nhl > h.level:
                    oh = h
                    if h.children:
                        h = h.children[-1]
                    else:
                        break
                np = h if nhl > h.level else oh

                # append current heading to new heading
                np.children.append(current_heading, taint=False)

                # if children are not included, distribute them among the
                # parent heading and it's siblings
                if not including_children:
                    for h in current_heading.children[:]:
                        if h and h.level <= nhl:
                            cls._append_heading(h, np)
                            current_heading.children.remove(h, taint=False)
        else:
            # promotion
            if p and nhl <= p.level:
                idx = current_heading.get_index_in_parent_list() + 1
                # find the new parent heading
                oh = p
                h = p
                while nhl <= h.level:
                    # append new children to current heading
                    for child in h.children[idx:]:
                        cls._append_heading(child, current_heading)
                    h.children.remove_slice(idx, len(h.children), taint=False)
                    idx = h.get_index_in_parent_list() + 1
                    if h.parent:
                        h = h.parent
                    else:
                        break
                ns = oh.next_sibling
                while ns and ns.level > current_heading.level:
                    nns = ns.next_sibling
                    cls._append_heading(ns, current_heading)
                    ns = nns

                # append current heading to new parent heading / document
                pl.remove(current_heading, taint=False)
                if nhl > h.level:
                    h.children.insert(idx, current_heading, taint=False)
                else:
                    d.headings.insert(idx, current_heading, taint=False)

        d.write()

        # restore cursor position
        vim.current.window.cursor = (c[0], c[1] + level)

        return True

    @classmethod
    @realign_tags
    @repeat
    @apply_count
    def demote_heading(cls, including_children=True, on_heading=False, insert_mode=False):
        if cls._change_heading_level(1, including_children=including_children, on_heading=on_heading, insert_mode=insert_mode):
            if including_children:
                return 'OrgDemoteSubtree'
            return 'OrgDemoteHeading'

    @classmethod
    @realign_tags
    @repeat
    @apply_count
    def promote_heading(cls, including_children=True, on_heading=False, insert_mode=False):
        if cls._change_heading_level(-1, including_children=including_children, on_heading=on_heading, insert_mode=insert_mode):
            if including_children:
                return 'OrgPromoteSubtreeNormal'
            return 'OrgPromoteHeadingNormal'

    @classmethod
    def _move_heading(cls, direction=Direction.FORWARD, including_children=True):
        """ Move heading up or down

        :returns: heading or None
        """
        d = ORGMODE.get_document()
        current_heading = d.current_heading()
        if not current_heading or \
            (direction == Direction.FORWARD and not current_heading.next_sibling) or \
            (direction == Direction.BACKWARD and not current_heading.previous_sibling):
            return None

        cursor_offset = vim.current.window.cursor[0] - (current_heading._orig_start + 1)
        l = current_heading.get_parent_list()
        if l is None:
            raise HeadingDomError('Current heading is not properly linked in DOM')

        if not including_children:
            if current_heading.previous_sibling:
                npl = current_heading.previous_sibling.children
                for child in current_heading.children:
                    npl.append(child, taint=False)
            elif current_heading.parent:
                # if the current heading doesn't have a previous sibling it
                # must be the first heading
                np = current_heading.parent
                for child in current_heading.children:
                    cls._append_heading(child, np)
            else:
                # if the current heading doesn't have a parent, its children
                # must be added as top level headings to the document
                npl = l
                for child in current_heading.children[::-1]:
                    npl.insert(0, child, taint=False)
            current_heading.children.remove_slice(0, len(current_heading.children), taint=False)

        idx = current_heading.get_index_in_parent_list()
        if idx is None:
            raise HeadingDomError('Current heading is not properly linked in DOM')

        offset = 1 if direction == Direction.FORWARD else -1
        del l[idx]
        l.insert(idx + offset, current_heading)

        d.write()

        vim.current.window.cursor = (
            current_heading.start_vim + cursor_offset,
            vim.current.window.cursor[1])

        return True

    @classmethod
    @repeat
    @apply_count
    def move_heading_upward(cls, including_children=True):
        if cls._move_heading(direction=Direction.BACKWARD, including_children=including_children):
            if including_children:
                return 'OrgMoveSubtreeUpward'
            return 'OrgMoveHeadingUpward'

    @classmethod
    @repeat
    @apply_count
    def move_heading_downward(cls, including_children=True):
        if cls._move_heading(direction=Direction.FORWARD, including_children=including_children):
            if including_children:
                return 'OrgMoveSubtreeDownward'
            return 'OrgMoveHeadingDownward'

    def register(self):
        """
        Registration of plugin. Key bindings and other initialization should be done.
        """
# EditStructure related default settings
        settings.set('org_improve_split_heading', '1')
# EditStructure related keybindings
        self.keybindings.append(Keybinding('<C-S-CR>',
                                     Plug('OrgNewHeadingAboveNormal', ':silent! %s ORGMODE.plugins["EditStructure"].new_heading(below=False)<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('New Heading &above', self.keybindings[-1])
        self.keybindings.append(Keybinding('<localleader>hN', '<Plug>OrgNewHeadingAboveNormal', mode=MODE_NORMAL))
        self.keybindings.append(Keybinding('<localleader><CR>', '<Plug>OrgNewHeadingAboveNormal', mode=MODE_NORMAL))

        self.keybindings.append(Keybinding('<S-CR>',
                                     Plug('OrgNewHeadingBelowNormal', ':silent! %s ORGMODE.plugins["EditStructure"].new_heading(below=True)<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('New Heading &below', self.keybindings[-1])
        self.keybindings.append(Keybinding('<localleader>hh', '<Plug>OrgNewHeadingBelowNormal', mode=MODE_NORMAL))
        self.keybindings.append(Keybinding('<localleader><CR>', '<Plug>OrgNewHeadingBelowNormal', mode=MODE_NORMAL))

        self.keybindings.append(Keybinding('<C-CR>', Plug('OrgNewHeadingBelowAfterChildrenNormal', ':silent! %s ORGMODE.plugins["EditStructure"].new_heading(below=True, end_of_last_child=True)<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('New Heading below, after &children', self.keybindings[-1])
        self.keybindings.append(Keybinding('<localleader>hn', '<Plug>OrgNewHeadingBelowAfterChildrenNormal', mode=MODE_NORMAL))
        self.keybindings.append(Keybinding('<CR>', '<Plug>OrgNewHeadingBelowAfterChildrenNormal', mode=MODE_NORMAL))

        self.keybindings.append(Keybinding('<C-S-CR>', Plug('OrgNewHeadingAboveInsert', '<C-o>:<C-u>silent! %s ORGMODE.plugins["EditStructure"].new_heading(below=False, insert_mode=True)<CR>' % VIM_PY_CALL, mode=MODE_INSERT)))
        self.keybindings.append(Keybinding('<S-CR>', Plug('OrgNewHeadingBelowInsert', '<C-o>:<C-u>silent! %s ORGMODE.plugins["EditStructure"].new_heading(below=True, insert_mode=True)<CR>' % VIM_PY_CALL, mode=MODE_INSERT)))
        self.keybindings.append(Keybinding('<C-CR>', Plug('OrgNewHeadingBelowAfterChildrenInsert', '<C-o>:<C-u>silent! %s ORGMODE.plugins["EditStructure"].new_heading(insert_mode=True, end_of_last_child=True)<CR>' % VIM_PY_CALL, mode=MODE_INSERT)))

        self.menu + Separator()

        self.keybindings.append(Keybinding('m{', Plug('OrgMoveHeadingUpward',
                                                 '%s ORGMODE.plugins["EditStructure"].move_heading_upward(including_children=False)<CR>' % VIM_PY_CALL)))
        self.keybindings.append(Keybinding('m[[',
                                     Plug('OrgMoveSubtreeUpward', '%s ORGMODE.plugins["EditStructure"].move_heading_upward()<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('Move Subtree &Up', self.keybindings[-1])
        self.keybindings.append(Keybinding('m}',
                                     Plug('OrgMoveHeadingDownward', '%s ORGMODE.plugins["EditStructure"].move_heading_downward(including_children=False)<CR>' % VIM_PY_CALL)))
        self.keybindings.append(Keybinding('m]]',
                                     Plug('OrgMoveSubtreeDownward', '%s ORGMODE.plugins["EditStructure"].move_heading_downward()<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('Move Subtree &Down', self.keybindings[-1])

        self.menu + Separator()

        self.menu + ActionEntry('&Copy Heading', 'yah', 'yah')
        self.menu + ActionEntry('C&ut Heading', 'dah', 'dah')

        self.menu + Separator()

        self.menu + ActionEntry('&Copy Subtree', 'yar', 'yar')
        self.menu + ActionEntry('C&ut Subtree', 'dar', 'dar')
        self.menu + ActionEntry('&Paste Subtree', 'p', 'p')

        self.menu + Separator()

        self.keybindings.append(Keybinding('<ah', Plug('OrgPromoteHeadingNormal', ':silent! %s ORGMODE.plugins["EditStructure"].promote_heading(including_children=False)<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('&Promote Heading', self.keybindings[-1])
        self.keybindings.append(Keybinding('<<', Plug('OrgPromoteOnHeadingNormal', ':silent! %s ORGMODE.plugins["EditStructure"].promote_heading(including_children=False, on_heading=True)<CR>' % VIM_PY_CALL)))
        self.keybindings.append(Keybinding('<{', '<Plug>OrgPromoteHeadingNormal', mode=MODE_NORMAL))
        self.keybindings.append(Keybinding('<ih', '<Plug>OrgPromoteHeadingNormal', mode=MODE_NORMAL))

        self.keybindings.append(Keybinding('<ar', Plug('OrgPromoteSubtreeNormal', ':silent! %s ORGMODE.plugins["EditStructure"].promote_heading()<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('&Promote Subtree', self.keybindings[-1])
        self.keybindings.append(Keybinding('<[[', '<Plug>OrgPromoteSubtreeNormal', mode=MODE_NORMAL))
        self.keybindings.append(Keybinding('<ir', '<Plug>OrgPromoteSubtreeNormal', mode=MODE_NORMAL))

        self.keybindings.append(Keybinding('>ah', Plug('OrgDemoteHeadingNormal', ':silent! %s ORGMODE.plugins["EditStructure"].demote_heading(including_children=False)<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('&Demote Heading', self.keybindings[-1])
        self.keybindings.append(Keybinding('>>', Plug('OrgDemoteOnHeadingNormal', ':silent! %s ORGMODE.plugins["EditStructure"].demote_heading(including_children=False, on_heading=True)<CR>' % VIM_PY_CALL)))
        self.keybindings.append(Keybinding('>}', '<Plug>OrgDemoteHeadingNormal', mode=MODE_NORMAL))
        self.keybindings.append(Keybinding('>ih', '<Plug>OrgDemoteHeadingNormal', mode=MODE_NORMAL))

        self.keybindings.append(Keybinding('>ar', Plug('OrgDemoteSubtreeNormal', ':silent! %s ORGMODE.plugins["EditStructure"].demote_heading()<CR>' % VIM_PY_CALL)))
        self.menu + ActionEntry('&Demote Subtree', self.keybindings[-1])
        self.keybindings.append(Keybinding('>]]', '<Plug>OrgDemoteSubtreeNormal', mode=MODE_NORMAL))
        self.keybindings.append(Keybinding('>ir', '<Plug>OrgDemoteSubtreeNormal', mode=MODE_NORMAL))

        # other keybindings
        self.keybindings.append(Keybinding('<C-d>', Plug('OrgPromoteOnHeadingInsert', '<C-o>:silent! %s ORGMODE.plugins["EditStructure"].promote_heading(including_children=False, on_heading=True, insert_mode=True)<CR>' % VIM_PY_CALL, mode=MODE_INSERT)))
        self.keybindings.append(Keybinding('<C-t>', Plug('OrgDemoteOnHeadingInsert', '<C-o>:silent! %s ORGMODE.plugins["EditStructure"].demote_heading(including_children=False, on_heading=True, insert_mode=True)<CR>' % VIM_PY_CALL, mode=MODE_INSERT)))
