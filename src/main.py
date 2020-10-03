from MediaWikiDumpReader import MediaWikiDumpReader as DumpReader
import os.path


def load_gazeteer(gazeteer_path):
    file = open(gazeteer_path, "r")
    keywords = file.read().lower().split('\n')
    file.close()
    return keywords

if __name__ == "__main__":
    current_directory = os.path.dirname(__file__)
    parent_directory = os.path.split(current_directory)[0]

    xml_path = "D:/skola/enwiki/enwiki_dump.xml"
    firstname_path = os.path.join(parent_directory, 'data', 'firstnames.txt', )
    surename_path = os.path.join(parent_directory, 'data', 'surenames.txt', )

    # load gazeteers
    gazeteers = {}

    gazeteers['firstnames'] = load_gazeteer(firstname_path)
    gazeteers['surenames'] = load_gazeteer(surename_path)

    with open(xml_path, 'rb') as in_xml:
        for record in DumpReader(in_xml, gazeteers):
            print("record:{}".format(record))



