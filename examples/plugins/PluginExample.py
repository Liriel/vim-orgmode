
from orgmode import ORGMODE
from orgmode.keybinding import Command, Keybinding, Plug
from orgmode.menu import ActionEntry, Submenu


class Example:
    """
    Example plugin.

    TODO: Extend this doc!
    """

    def __init__(self):
        """ Initialize plugin """
        object.__init__(self)
        # menu entries this plugin should create
        self.menu = ORGMODE.orgmenu + Submenu('Example')

        # key bindings for this plugin
        # key bindings are also registered through the menu so only additional
        # bindings should be put in this variable
        self.keybindings = []

        # commands for this plugin
        self.commands = []

    @classmethod
    def action(cls):
        """
        Some kind of action.

        :returns: TODO
        """
        pass

    def register(self):
        """
        Registration of the plugin.

        Key bindings and other initialization should be done here.
        """
        # an Action menu entry which binds "keybinding" to action ":action"
        self.commands.append(Command('OrgActionCommand',
                ':py ORGMODE.plugins["Example"].action()'))
        self.keybindings.append(Keybinding('keybinding',
                Plug('OrgAction', self.commands[-1])))
        self.menu + ActionEntry('&Action', self.keybindings[-1])
