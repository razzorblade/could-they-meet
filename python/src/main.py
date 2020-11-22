from wiki_reader import MediaWikiDumpReader as DumpReader
from wiki_splitter import MediaWikiDumpSplitter
import os.path
import utils

RUN_SPLIT = False
SPLIT_SIZE = 2000000000


def load_gazetteer(gazetteer_path):
    file = open(gazetteer_path, "r")
    keywords = file.read().lower().split('\n')
    file.close()
    return keywords


if __name__ == "__main__":

    current_directory = os.path.dirname(__file__)
    parent_directory = os.path.split(current_directory)[0]

    firstname_path = os.path.join(parent_directory, 'data', 'firstnames.txt', )
    surname_path = os.path.join(parent_directory, 'data', 'surnames.txt', )
    dump_split_path = os.path.join(parent_directory, 'data', 'dump_split.xml')
    exported_path = os.path.join(parent_directory, 'data', 'dump_export.txt')
    xml_path = "D:/skola/enwiki/enwiki_dump.xml"

    if RUN_SPLIT:
        splitter = MediaWikiDumpSplitter(xml_path, dump_split_path, SPLIT_SIZE)
        splitter.export_chunk()
        exit(0)

    # load gazetteers
    gazetteers = {'firstnames': load_gazetteer(firstname_path), 'surnames': load_gazetteer(surname_path)}

    with open(dump_split_path, 'rb') as in_xml:
        for record in DumpReader(dump_split_path, in_xml, gazetteers, (True, exported_path)):
           # print("record:{}".format(record))
            pass