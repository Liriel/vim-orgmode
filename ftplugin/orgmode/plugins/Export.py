# -*- coding: utf-8 -*-

import os
import subprocess

import vim

from orgmode._vim import ORGMODE, echoe, echom
from orgmode.menu import Submenu, ActionEntry, add_cmd_mapping_menu
from orgmode.keybinding import Keybinding, Plug, Command, VIM_PY_CALL
from orgmode import settings


class Export(object):
    """
    Export a orgmode file using emacs orgmode.

    This is a *very simple* wrapper of the emacs/orgmode export.  emacs and
    orgmode need to be installed. We simply call emacs with some options to
    export the .org.

    TODO: Offer export options in vim. Don't use the menu.
    TODO: Maybe use a native implementation.
    """

    def __init__(self):
        """ Initialize plugin """
        object.__init__(self)
        # menu entries this plugin should create
        self.menu = ORGMODE.orgmenu + Submenu('Export')

        # key bindings for this plugin
        # key bindings are also registered through the menu so only additional
        # bindings should be put in this variable
        self.keybindings = []

        # commands for this plugin
        self.commands = []

    @classmethod
    def _get_init_script(cls):
        init_script = settings.get('org_export_init_script', '')
        if init_script:
            init_script = os.path.expandvars(os.path.expanduser(init_script))
            if os.path.exists(init_script):
                return init_script
            else:
                echoe('Unable to find init script %s' % init_script)

    @classmethod
    def _export(cls, format_):
        """Export current file to format.

        Args:
            format_: pdf or html

        Returns:
            return code
        """
        emacsbin = os.path.expandvars(os.path.expanduser(
            settings.get('org_export_emacs', '/usr/bin/emacs')))
        if not os.path.exists(emacsbin):
            echoe('Unable to find emacs binary %s' % emacsbin)

        # build the export command
        cmd = [
            emacsbin,
            '-nw',
            '--batch',
            '--visit=%s' % vim.eval('expand("%:p")'),
            '--funcall=%s' % format_
        ]
        # source init script as well
        init_script = cls._get_init_script()
        if init_script:
            cmd.extend(['--script', init_script])

        # export
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        if p.returncode != 0 or settings.get('org_export_verbose') == 1:
            echom('\n'.join(map(lambda x: x.decode(), p.communicate())))
        return p.returncode

    @classmethod
    def topdf(cls):
        """Export the current buffer as pdf using emacs orgmode."""
        ret = cls._export('org-latex-export-to-pdf')
        if ret != 0:
            echoe('PDF export failed.')
        else:
            echom('Export successful: %s.%s' % (vim.eval('expand("%:r")'), 'pdf'))

    @classmethod
    def tobeamer(cls):
        """Export the current buffer as beamer pdf using emacs orgmode."""
        ret = cls._export('org-beamer-export-to-pdf')
        if ret != 0:
            echoe('PDF export failed.')
        else:
            echom('Export successful: %s.%s' % (vim.eval('expand("%:r")'), 'pdf'))

    @classmethod
    def tohtml(cls):
        """Export the current buffer as html using emacs orgmode."""
        ret = cls._export('org-html-export-to-html')
        if ret != 0:
            echoe('HTML export failed.')
        else:
            echom('Export successful: %s.%s' % (vim.eval('expand("%:r")'), 'html'))

    @classmethod
    def tolatex(cls):
        """Export the current buffer as latex using emacs orgmode."""
        ret = cls._export('org-latex-export-to-latex')
        if ret != 0:
            echoe('latex export failed.')
        else:
            echom('Export successful: %s.%s' % (vim.eval('expand("%:r")'), 'tex'))

    @classmethod
    def tomarkdown(cls):
        """Export the current buffer as markdown using emacs orgmode."""
        ret = cls._export('org-md-export-to-markdown')
        if ret != 0:
            echoe('Markdown export failed. Make sure org-md-export-to-markdown is loaded in emacs, see the manual for details.')
        else:
            echom('Export successful: %s.%s' % (vim.eval('expand("%:r")'), 'md'))

    def register(self):
        """Registration and keybindings."""

        # path to emacs executable
        settings.set('org_export_emacs', '/usr/bin/emacs')
        # verbose output for export
        settings.set('org_export_verbose', 0)
        # allow the user to define an initialization script
        settings.set('org_export_init_script', '')

        # to PDF
        add_cmd_mapping_menu(
            self,
            name='OrgExportToPDF',
            function=':%s ORGMODE.plugins["Export"].topdf()<CR>' % VIM_PY_CALL,
            key_mapping='<localleader>ep',
            menu_desrc='To PDF (via Emacs)'
        )
        # to Beamer PDF
        add_cmd_mapping_menu(
            self,
            name='OrgExportToBeamerPDF',
            function=':%s ORGMODE.plugins["Export"].tobeamer()<CR>' % VIM_PY_CALL,
            key_mapping='<localleader>eb',
            menu_desrc='To Beamer PDF (via Emacs)'
        )
        # to latex
        add_cmd_mapping_menu(
            self,
            name='OrgExportToLaTeX',
            function=':%s ORGMODE.plugins["Export"].tolatex()<CR>' % VIM_PY_CALL,
            key_mapping='<localleader>el',
            menu_desrc='To LaTeX (via Emacs)'
        )
        # to HTML
        add_cmd_mapping_menu(
            self,
            name='OrgExportToHTML',
            function=':%s ORGMODE.plugins["Export"].tohtml()<CR>' % VIM_PY_CALL,
            key_mapping='<localleader>eh',
            menu_desrc='To HTML (via Emacs)'
        )
        # to Markdown
        add_cmd_mapping_menu(
            self,
            name='OrgExportToMarkdown',
            function=':%s ORGMODE.plugins["Export"].tomarkdown()<CR>' % VIM_PY_CALL,
            key_mapping='<localleader>em',
            menu_desrc='To Markdown (via Emacs)'
        )
