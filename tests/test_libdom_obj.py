import unittest

from orgmode.liborgmode.dom_obj import DomObj


class DomObjTestCase(unittest.TestCase):
    def test_str(self):
        # used to raise NameError: name 'level' is not defined
        self.assertEqual(str(DomObj(level=2, title='A title')), '<dom obj level=2, title=A title>')

    def test_str_defaults(self):
        self.assertEqual(str(DomObj()), '<dom obj level=1, title=>')
