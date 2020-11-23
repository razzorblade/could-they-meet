from textwrap import wrap

from lxml import etree
from date_parsing.date_export import DateExport
from date_parsing.date_format import DateFormat
from utilities import utils
from utilities.runtime_constants import RuntimeConstants as Constants
from utilities.attr_type_constraint import auto_attr_check
import re
import html
import os
import sys


@auto_attr_check
class MediaWikiDumpReader:

    def __init__(self, file_path=str, xml_stream = str, gazetteers=(str, list), export_info=(bool, str), verbose = False):
        """
       Initialize dump reader to correctly read dump and use additional required information

       :param file_path: String path to unzipped xml dump file from wikipedia
       :param xml_stream: open() stream to xml file
       :param gazetteers: Gazetteers containing keywords for "firstnames" and "surnames"
       :param export_info: Info used to export found persons in wikipedia dump. This is a tuple of
                           bool and str telling whether to export to file and path to this file
       """
        self.context = etree.iterparse(xml_stream, events=("end",), tag=['{*}page'])
        self.gazetteers = gazetteers
        self.export_info = export_info
        self.size = os.path.getsize(file_path)
        self.verbose = verbose

    def __del__(self):
        if self.export_info[0] and not self.write_file.closed:
            self.write_file.close()

    def _start_parse(self):
        for event, element in self.context:
            yield event, element

            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]

    def __iter__(self):

        if self.export_info[0]:
            self.write_file = open(self.export_info[1], "w", encoding="utf-8")

        progress = 0
        print("Parser started on", utils.get_smart_file_size(self.size), "of data.")

        if self.verbose:
            utils.update_progress(0)

        for event, elem in self._start_parse():
            entity = {}
            export_flag = True

            # Get inner text
            inner_page = etree.tostring(elem).decode("UTF-8")

            # Report progress
            if self.verbose:
                progress += sys.getsizeof(inner_page) / self.size
                utils.update_progress(utils.max_clamp(progress, 0.9999))

            # Check if this page is a redirect to another page, therefore, processing will be skipped
            redirect_match = re.search("<redirect title=\"(.*)\"\/>", inner_page)
            if redirect_match:
                continue

            # Get title of this page
            exported_title = html.unescape(re.search("<title>([\s\S]*?)<\/title>", inner_page)[1])
            entity["name"] = exported_title

            birth_date_found = False
            death_date_found = False
            correct_age = False

            # Go line by line
            for line in wrap(html.unescape(inner_page), 5000):
                line = line.strip().lower()
                try:
                    # Try to find birth and death dates in current line
                    if not birth_date_found:
                        (birth_date_found, birth_date) = self.extract_birth_date(line, exported_title)
                    if not death_date_found:
                        (death_date_found, death_date) = self.extract_death_date(line, exported_title)

                    # If nothing was found, do text search
                    if not birth_date_found and not death_date_found:
                        (birth_date_found, birth_date, death_date_found, death_date) = self.extract_fulltext_dates(inner_page, line, exported_title)

                    # Set entity fields if dates were found. If death date not found, do
                    # additional statistical check whether person is still alive
                    if birth_date_found:
                        entity["birth_date"] = birth_date

                    if death_date_found:
                        entity["death_date"] = death_date
                    elif birth_date_found:
                        # Person that does not have death date might be alive
                        if Constants.CURRENT_YEAR - birth_date.year <= Constants.MAXIMUM_ALLOWED_AGE:
                            entity["death_date"] = "alive"
                            death_date = "alive"
                            death_date_found = True

                    # Update export_flag. We wont have to search for more, if both dates were found
                    export_flag = birth_date_found and death_date_found
                    if export_flag:
                        correct_age = DateExport.is_correct_age(birth_date, death_date)
                        break
                except:
                    # Any error during export
                    if self.verbose:
                        print("\nRecovering from export error caused at", exported_title, "...")

                    export_flag = False

            if export_flag and correct_age:
                if self.export_info[0]:
                    write_str = entity["name"] + "," + entity["birth_date"].__repr__() + "," + entity["death_date"].__repr__() + "\n"
                    self.write_file.write(write_str)
                yield entity

        if self.export_info[0]:
            self.write_file.close()

        if self.verbose:
            utils.update_progress(1)

    @staticmethod
    def extract_birth_date(line, title):
        """
        Matches a birth date from line using regex

        :param title: Name of entity
        :param line: String with wikipedia text from which birth date will be exported, if present
        """
        if ("birth date" in line or "birth_date" in line or "birth-date" in line) and "infobox" in line:
            # birth is in format [1]year [2]month [3]day
            birth_date_match = re.search(
                r"(?:birth date|birth date and age|birth-date|birth_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2})",
                line)
            if birth_date_match:
                return True, DateExport(int(birth_date_match[1]), int(birth_date_match[2]), int(birth_date_match[3]))

            # another format in infobox: birth-date|23 September 1996  or  birth-date = 6 November AD 19
            birth_date_match = re.search(
                r"(?:birth date|birth-date|birth_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\W+(\d{1,2})(?: or?\W+\d{1,2})?\W+([a-zA-Z]+)\W*?(?:ad)?\W*?(\d{1,4})\s*(bc)?",
                line)
            if birth_date_match:
                try:
                    date = DateExport.from_format(
                        birth_date_match[1] + " " + birth_date_match[2] + " " + birth_date_match[3],
                        DateFormat.TXTMONTH_FULL)
                except:
                    pass
                else:
                    if birth_date_match[4] and "bc" in birth_date_match[4]:
                        date.BC = True
                    return True, date

            # another format in infobox: birth-date|September 23, 1996
            birth_date_match = re.search(
                r"(?:birth date|birth-date|birth_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\W+([a-zA-Z]+)\W+(\d{1,2})(?: or?\W+\d{1,2})?\W+(\d{1,4})\s*(bc)?",
                line)
            if birth_date_match:
                try:
                    date = DateExport.from_format(
                        birth_date_match[2] + " " + birth_date_match[1] + " " + birth_date_match[3],
                        DateFormat.TXTMONTH_FULL)
                except:
                    pass
                else:
                    if birth_date_match[4] and "bc" in birth_date_match[4]:
                        date.BC = True
                    return True, date

            # another format in infobox: birth-date = {{circa 650}} BC
            birth_date_match = re.search(
                r"(?:birth-date|birth_date|birth date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|?(?:c\.|circa\W*)?([0-9]{1,4}).+?\}\}.*?(bc)",
                line)
            if birth_date_match:
                date = DateExport.from_format(birth_date_match[1], DateFormat.YEAR_ONLY)
                date.BC = True
                return True, date

            # another format in infobox: birth-date = circa 650 BC
            birth_date_match = re.search(
                r"(?:birth-date|birth_date|birth date)\W*(?:c\.|circa\W*) ([0-9]{1,4}) (bc)",
                line)
            if birth_date_match:
                date = DateExport.from_format(birth_date_match[1], DateFormat.YEAR_ONLY)
                date.BC = True
                return True, date

            # another format in infobox: birth-date = circa 650
            birth_date_match = re.search(
                r"(?:birth-date|birth_date|birth date)\W*(?:c\.|circa\W*) ([0-9]{1,4})[a-zA-Z0-9\W]*?\|",
                line)
            if birth_date_match:
                date = DateExport.from_format(birth_date_match[1], DateFormat.YEAR_ONLY)
                return True, date

            # another format in infobox: birth-date|c. 1750  or  birth-date|1950
            birth_date_match = re.search(r"(?:birth-date|birth_date|birth date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|(?:c.\W*)?([0-9]{1,4})", line)
            if birth_date_match:
                return True, DateExport.from_format(birth_date_match[1], DateFormat.YEAR_ONLY)

            # another format in infobox: birth-date|May, 1920
            birth_date_match = re.search(r"(?:birth-date|birth_date|birth date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n))?\|([a-zA-Z]+)(?:\W+|,)([0-9]{1,4})", line)
            if birth_date_match:
                return True, DateExport.from_format(birth_date_match[1] + " " + birth_date_match[2], DateFormat.TXTMONTH_AND_YEAR)

            # another format in infobox: birth year and age|1750
            birth_date_match = re.search(r"birth year and age\W*?\|(\d{1,4})", line)
            if birth_date_match:
                return True, DateExport.from_format(birth_date_match[1], DateFormat.YEAR_ONLY)

        return False, None

    @staticmethod
    def extract_death_date(line, title):
        """
        Matches a death date from line using regex

        :param title:
        :param line: String with wikipedia text from which death date will be exported, if present
        """
        if ("death date" in line or "death_date" in line or "death-date" in line)  and "infobox" in line:

            # another format in infobox: death-date|1875 12 1   -> YYYY MM DD
            death_date_match = re.search(
                r"(?:death date|death date and age|death-date|death_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2})\s*\|",
                line)
            if death_date_match:
                return True, DateExport(int(death_date_match[1]), int(death_date_match[2]), int(death_date_match[3]))

            # another format in infobox: death-date|23 September 1996
            death_date_match = re.search(
                r"(?:death date|death-date|death_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\W+(\d{1,2})(?: or?\W+\d{1,2})?\W+([a-zA-Z]+)\W*?(?:ad)?\W*?(\d{1,4})\s*(bc)?",
                line)
            if death_date_match:
                try:
                    date = DateExport.from_format(
                        death_date_match[1] + " " + death_date_match[2] + " " + death_date_match[3],
                        DateFormat.TXTMONTH_FULL)
                except:
                    pass
                else:
                    if death_date_match[4] and "bc" in death_date_match[4]:
                        date.BC = True

                    return True, date

            # another format in infobox: birth-date = {{circa 650}} BC
            death_date_match = re.search(
                r"(?:death-date|death_date|death date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|?(?:c\.|circa\W*)?([0-9]{1,4}).+?\}\}.*?(bc)",
                line)
            if death_date_match:
                date = DateExport.from_format(death_date_match[1], DateFormat.YEAR_ONLY)
                date.BC = True
                return True, date

            # another format in infobox: death-date = circa 650 BC
            death_date_match = re.search(
                r"(?:death-date|death_date|death date).*(?:c\.|circa\W*) ([0-9]{1,4}) (bc)",
                line)
            if death_date_match:
                date = DateExport.from_format(death_date_match[1], DateFormat.YEAR_ONLY)
                date.BC = True
                return True, date

            # another format in infobox: death-date = circa 650
            death_date_match = re.search(
                r"(?:death-date|death_date|death date)\W*(?:c\.|circa\W*) ([0-9]{1,4})[a-zA-Z0-9\W]*?\|",
                line)
            if death_date_match:
                date = DateExport.from_format(death_date_match[1], DateFormat.YEAR_ONLY)
                return True, date

            # another format in infobox: death-date|September 23, 1996
            death_date_match = re.search(
                r"(?:death date|death-date|death_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\W+([a-zA-Z]+)\W+(\d{1,2})(?: or?\W+\d{1,2})?\W+(\d{1,4})\s*(bc)?",
                line)
            if death_date_match:
                try:
                    date = DateExport.from_format(death_date_match[2] + " " + death_date_match[1] + " " + death_date_match[3],DateFormat.TXTMONTH_FULL)
                except:
                    pass
                else:
                    if death_date_match[4] and "bc" in death_date_match[4]:
                        date.BC = True
                    return True, date

            # another format in infobox: death-date|1940  or  death date|mf=n|904
            death_date_match = re.search(r"(?:death-date|death_date|death date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|(?:c.\W*)?([0-9]{1,4})", line)
            if death_date_match:
                return True, DateExport.from_format(death_date_match[1], DateFormat.YEAR_ONLY)

            # another format in infobox: death-date|May, 1920  or  death_date|mf=yes|January,1205
            death_date_match = re.search(r"(?:death-date|death_date|death date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n))?\|([a-zA-Z]+)(?:\W+|,)([0-9]{1,4})", line)
            if death_date_match:
                return True, DateExport.from_format(death_date_match[1] + " " + death_date_match[2], DateFormat.TXTMONTH_AND_YEAR)

            # another format in infobox: birth year and age|1750
            death_date_match = re.search(r"death year and age\W*?\|(\d{1,4})", line)
            if death_date_match:
                return True, DateExport.from_format(death_date_match[1], DateFormat.YEAR_ONLY)

        return False, None

    @staticmethod
    def extract_fulltext_dates(fulltext, line, title):
        """
        Matches a death date from line using regex

        :param title:
        :param line: String with wikipedia text from which dates will be exported, if present
        """


        # Check if it is a person
        person_check = re.search(
            r"\[\[Category:.*?(births|actors|actor|people|winner|winners|woman|women|man|men|singers|singer|politician|deaths|photographers|artists|wrestlers|)\]\]",
            fulltext)

        is_person = False
        if person_check:
            for p in person_check.groups():
                if p != "":
                    is_person = True


        if is_person:
            # Replace special chars so we can reduce amount of cases in regex
            rep = {"&ndash;": "-", "&nbsp;": " ", "{{snd}}" : "-"}
            rep = dict((re.escape(k), v) for k, v in rep.items())
            pattern = re.compile("|".join(rep.keys()))
            line = pattern.sub(lambda m: rep[re.escape(m.group(0))], line)

            # Try to find birth date in text
            # FORMAT: Name Surname (DD Month YYYY {{snd}} DD Month YYYY)
            match = re.search(title.lower() + r"\W+\((\d{1,2})\W+([a-zA-Z]+)\W+?(\d+)\W*?(?:-| |to)\W*?(\d{1,2})\W+?([a-zA-Z]+)\W+(\d+).*?\)", line)

            if match:
                birth = DateExport(int(match[3]),DateExport.month_to_num(match[2]), int(match[1]))
                death = DateExport(int(match[6]),DateExport.month_to_num(match[5]), int(match[4]))
                return True, birth, True, death

            # FORMAT: Name Surname (YYYY-YYYY)
            match = re.search(title.lower() + r"\W+\(([0-9]+).*?([0-9]+)\)",line)
            if match:
                return True, DateExport.from_format(match[1], DateFormat.YEAR_ONLY), True, DateExport.from_format(match[2], DateFormat.YEAR_ONLY)

            # FORMAT: Name Surname (texttext c. YYYY - c. YYYY texttext)
            match = re.search(title.lower() + r"\W*\(.*(?:c.|circa)\W*(\d+)\W*(?:c.|circa)\W*(\d+).*\)", line)
            if match:
                return True, DateExport.from_format(match[1], DateFormat.YEAR_ONLY), True, DateExport.from_format(
                    match[2], DateFormat.YEAR_ONLY)

         #   # FORMAT: Name (names...) Surname (born Month DD, YYYY)
         #   birth_date_match = re.search("([a-zA-Z\W]*) born ([a-zA-Z]+ \d{1,2},\W*\d{4})", line)

         #   # Check if the title has something common with person's name in the .* previous content of the line
         #   person_name_split = title.split(' ')
         #   if all(elem in birth_date_match[0] for elem in person_name_split):
         #       # export date
         #       print("some new match on", title)
         #       return True, DateExport.from_format(birth_date_match[2], DateFormat.AS_TEXT)

        return False, None, False, None