from parsers.wiki_reader import MediaWikiDumpReader as DumpReader
from parsers.wiki_splitter import MediaWikiDumpSplitter
from utilities.runtime_constants import RuntimeConstants as Constants
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

def main(argv):
    # Options and their arguments
    opts, args = getopt.getopt(sys.argv[1:], "", ["input=", "output=", "verbose", "splitter="])

    output_file = None
    input_file = None
    verbose = False
    run_split = False
    split_size = 0

    for o, a in opts:
        if o == "--verbose":
            verbose = True
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