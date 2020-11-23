from parsers.wiki_reader import MediaWikiDumpReader as DumpReader
from parsers.wiki_splitter import MediaWikiDumpSplitter
from utilities.runtime_constants import RuntimeConstants as Constants
from utilities.utils import get_smart_file_size
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

def search_person(file):
    name1 = input("Enter name of first person:  ")
    name2 = input("Enter name of second person: ")

    n1_found, n2_found = False, False

    with open(file, 'r') as read_obj:
        for line in read_obj:
            # For each line, check if line contains the string
            if not n1_found and name1 in line:
                n1_found = True
                print(line.replace("\n",""))
            if not n2_found and name2 in line:
                n2_found = True
                print(line.replace("\n",""))

            if n1_found and n2_found:
                break

    if not n1_found:
        print("Could not find person", name1)
    if not n2_found:
        print("Could not find person", name2)

def main(argv):
    # Options and their arguments
    opts, args = getopt.getopt(sys.argv[1:], "", ["input=", "output=", "verbose", "splitter=", "search"])

    output_file = None
    input_file = None
    verbose = False
    run_split = False
    split_size = 0
    search = False

    for o, a in opts:
        if o == "--verbose":
            verbose = True
        elif o == "--search":
            search = True
        elif o == "--output":
            output_file = a
        elif o == "--input":
            input_file = a
        elif o == "--splitter":
            run_split = True
            try:
                split_size = int(a)
            except:
                print("Split size is not in correct format.")
                exit(1)

    if search:
        search_person(input_file)
        exit(0)

    # If running from PyCharm
    if output_file is None or input_file is None:
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.split(current_directory)[0]

        try:
            firstname_path = os.path.join(parent_directory, 'data', 'firstnames.txt', )
            surname_path = os.path.join(parent_directory, 'data', 'surnames.txt', )
            input_file = os.path.join(parent_directory, 'data', 'dump_split.xml')
            output_file = os.path.join(parent_directory, 'data', 'dump_export.txt')

            ########## Debugging
            whole_wiki = "D:/skola/enwiki/enwiki_dump.xml"
            ##########

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

    # load gazetteers
    # gazetteers = {'firstnames': load_gazetteer(firstname_path), 'surnames': load_gazetteer(surname_path)}

    with open(input_file, 'rb') as in_xml:
        for record in DumpReader(input_file, in_xml, None, (True, output_file), verbose):
            #  print("record:{}".format(record))
            pass

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main(sys.argv[1:])
