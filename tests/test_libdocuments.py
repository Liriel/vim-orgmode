import unittest

from orgmode.liborgmode.documents import Document
from orgmode.liborgmode.headings import Heading


class DocumentStrTestCase(unittest.TestCase):
    def setUp(self):
        self.document = Document()
        self.document.headings.append(Heading(title='First', body=['body 1']))
        self.document.headings.append(Heading(title='Second'))

    def test_str_without_meta_information(self):
        self.assertEqual(str(self.document), '* First\nbody 1\n* Second')

    def test_str_with_meta_information(self):
        self.document.meta_information = ['#+TITLE: Test']
        self.assertEqual(str(self.document), '#+TITLE: Test\n* First\nbody 1\n* Second')

    def test_str_with_children(self):
        self.document.headings[0].children.append(Heading(level=2, title='Child', body=['child body']))
        self.assertEqual(str(self.document), '* First\nbody 1\n** Child\nchild body\n* Second')

    def test_str_empty_document(self):
        self.assertEqual(str(Document()), '')
