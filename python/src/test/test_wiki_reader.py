from unittest import TestCase
from wiki_reader import MediaWikiDumpReader as DumpReader
import os
from pathlib import Path


class TestMediaWikiDumpReader(TestCase):

    def load_gazetteer(self, gazetteer_path):
        file = open(gazetteer_path, "r")
        keywords = file.read().lower().split('\n')
        file.close()
        return keywords

    def setUp(self):
        current_directory = os.path.dirname(__file__)
        path = Path(current_directory)
        parent_directory = path.parent.parent

        firstname_path = os.path.join(parent_directory, 'data', 'firstnames.txt', )
        surname_path = os.path.join(parent_directory, 'data', 'surnames.txt', )
        dump_split_path = os.path.join(parent_directory, 'data', 'dump_split.xml')
        exported_path = os.path.join(parent_directory, 'data', 'dump_export.txt')
        xml_path = "D:/skola/enwiki/enwiki_dump.xml"
        gazetteers = {'firstnames': self.load_gazetteer(firstname_path), 'surnames': self.load_gazetteer(surname_path)}

        self.in_xml = open(dump_split_path, 'rb')
        self.reader = DumpReader(self.in_xml, gazetteers, (True, exported_path))

    def tearDown(self):
        self.in_xml.close()
        self.reader = None

class TestRead(TestMediaWikiDumpReader):

    def test_export_first_lines(self):
        count = 0
        for record in self.reader:
            if count == 0:
                self.assertEqual(record["name"], "Abraham Lincoln")
                self.assertEqual(record["birth_date"].__repr__(), "12.2.1809")
                self.assertEqual(record["death_date"].__repr__(), "15.4.1865")
            elif count == 1:
                self.assertEqual(record["name"], "Ayn Rand")
                self.assertEqual(record["birth_date"].__repr__(), "2.2.1905")
                self.assertEqual(record["death_date"].__repr__(), "6.3.1982")

            if count > 1:
                break

            count += 1
