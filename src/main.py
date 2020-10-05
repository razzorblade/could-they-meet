from wiki_reader import MediaWikiDumpReader as DumpReader
import os.path


def load_gazetteer(gazetteer_path):
    file = open(gazetteer_path, "r")
    keywords = file.read().lower().split('\n')
    file.close()
    return keywords


if __name__ == "__main__":
    current_directory = os.path.dirname(__file__)
    parent_directory = os.path.split(current_directory)[0]

    xml_path = "D:/skola/enwiki/enwiki_dump.xml"
    firstname_path = os.path.join(parent_directory, 'data', 'firstnames.txt', )
    surname_path = os.path.join(parent_directory, 'data', 'surnames.txt', )

    # load gazetteers
    gazetteers = {'firstnames': load_gazetteer(firstname_path), 'surnames': load_gazetteer(surname_path)}

    with open(xml_path, 'rb') as in_xml:
        for record in DumpReader(in_xml, gazetteers):
            print("record:{}".format(record))

