from parsers.wiki_reader import MediaWikiDumpReader as DumpReader
from parsers.wiki_splitter import MediaWikiDumpSplitter
from utilities.runtime_constants import RuntimeConstants as Constants
from utilities.utils import get_smart_file_size
from search.export_search import ExportSearch
from date_parsing.date_export import DateExport
import os.path
import signal
import sys, getopt

def load_gazetteer(gazetteer_path):
    file = open(gazetteer_path, "r")
    keywords = file.read().lower().split('\n')
    file.close()
    return keywords

def signal_handler(sig, frame):
    print('\nParsing interrupted. All parsed content is in output file.')
    sys.exit(0)

def run_indexer(file, bulk_size):
    file = "../data/whole_wiki_parsed.txt"
    search = ExportSearch("people")
    search.prepare_elasticsearch()
    search.insert_data(file, bulk_size)
    print("Indexing is complete.")

def search_person():
    # name1 = input("Enter name of first person:  ")
    # name2 = input("Enter name of second person: ")
    search = ExportSearch("people")

    # To create index and build types
    #search.prepare_elasticsearch()

    # To build new index and insert all data from file
    #search.insert_data(file, 10000)

    name1 = input("Enter first name: ")
    res = search.find(name1)
    while not res[0]:
        name1 = input("Enter first name: ")
        res = search.find(name1)

    if res[0]:
        person1_name, person1_birth, person1_death = res[1], res[2], res[3]
        print(person1_name, person1_birth,  "-",person1_death)

    name2 = input("Enter second name: ")
    res = search.find(name2)
    while not res[0]:
        name2 = input("Enter second name: ")
        res = search.find(name2)

    if res[0]:
        person2_name, person2_birth, person2_death = res[1], res[2], res[3]
        print(person2_name, person2_birth, "-", person2_death)


    # now we have both people and their dates
    could_meet = DateExport.could_meet(person1_birth, person1_death, person2_birth, person2_death)

    if could_meet:
        print("These people could meet!")
    else:
        print("These people could not meet!")

def main(argv):
    # Options and their arguments
    opts, args = getopt.getopt(sys.argv[1:], "", ["input=", "output=", "verbose", "splitter=", "search", "search-indexer", "bulk="])

    output_file = None
    input_file = None
    verbose = False
    run_split = False
    split_size = 0
    search = False
    search_indexer = False
    bulk_size = 5000

    for o, a in opts:
        if o == "--verbose":
            verbose = True
        elif o == "--search":
            search = True
        elif o == "--search-indexer":
            search_indexer = True
        elif o == "--output":
            output_file = a
        elif o == "--input":
            input_file = a
        elif o == "--bulk":
            try:
                bulk_size = int(a)
            except:
                print("Bulk size is not in correct format.")
                exit(1)
        elif o == "--splitter":
            run_split = True
            try:
                split_size = int(a)
            except:
                print("Split size is not in correct format.")
                exit(1)

    if search:
        search_person()
        exit(0)

    if search_indexer:
        run_indexer(input_file,bulk_size)
        exit(0)

    # If running from PyCharm
    if output_file is None or input_file is None:
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.split(current_directory)[0]

        try:
            input_file = os.path.join(parent_directory, 'data', 'dump_split.xml')
            output_file = os.path.join(parent_directory, 'data', 'dump_export.txt')
        except FileNotFoundError:
            print("No input and output files were provided. Fallback /data/ folder did not find any files. Interrupting...")
            exit(1)

    # RUN_SPLIT for PyCharm development and run_split if called from console
    if Constants.RUN_SPLIT or run_split:
        if split_size == 0:
            # If PyCharm is currently running app, use Constants
            split_size = Constants.SPLIT_SIZE

        if verbose:
            print("Sorry, splitter is not able to track progress currently.")

        splitter = MediaWikiDumpSplitter(input_file, output_file, split_size)
        print("Splitter started export. Goal size is", get_smart_file_size(split_size))
        splitter.export_chunk()
        exit(0)

    with open(input_file, 'rb') as in_xml:
        for record in DumpReader(input_file, in_xml, None, (True, output_file), verbose):
            #print("record:{}".format(record))
            pass

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main(sys.argv[1:])
