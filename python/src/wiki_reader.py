from textwrap import wrap

from lxml import etree
from date_parsing.date_export import DateExport
from date_parsing.date_format import DateFormat
from runtime_constants import RuntimeConstants as Constants
from attr_type_constraint import auto_attr_check
import re
import html


@auto_attr_check
class MediaWikiDumpReader:

    def __init__(self, file_path=str, gazetteers=(str, list), export_info=(bool, str)):
        """
       Initialize dump reader to correctly read dump and use additional required information

       :param file_path: String path to unzipped xml dump file from wikipedia
       :param gazetteers: Gazetteers containing keywords for "firstnames" and "surnames"
       :param export_info: Info used to export found persons in wikipedia dump. This is a tuple of
                           bool and str telling whether to export to file and path to this file
       """
        self.context = etree.iterparse(file_path, events=("end",), tag=['{*}page'])
        self.gazetteers = gazetteers
        self.export_info = export_info

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

        for event, elem in self._start_parse():
            entity = {}
            export_flag = True

            # Get inner text
            inner_page = etree.tostring(elem).decode("UTF-8")

            # Check if this page is a redirect to another page, therefore, processing will be skipped
            redirect_match = re.search("<redirect title=\"(.*)\"\/>", inner_page)
            if redirect_match:
                continue

            # Get title of this page
            exported_title = html.unescape(re.search("<title>([\s\S]*?)<\/title>", inner_page)[1])
            entity["name"] = exported_title

            birth_date_found = False
            death_date_found = False

            # Go line by line
            for line in wrap(inner_page, 2000):

                line = line.strip().lower()

                # Try to find birth and death dates in current line
                if not birth_date_found:
                    (birth_date_found, birth_date) = self.extract_birth_date(line, exported_title)
                if not death_date_found:
                    (death_date_found, death_date) = self.extract_death_date(line, exported_title)

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
                        death_date_found = True

                # Update export_flag. We wont have to search for more, if both dates were found
                export_flag = birth_date_found and death_date_found
                if export_flag:
                    break

            if export_flag:
                if self.export_info[0]:
                    write_str = entity["name"] + "," + entity["birth_date"].__repr__() + "," + entity["death_date"].__repr__() + "\n"
                    # noinspection PyUnboundLocalVariable
                    self.write_file.write(write_str)
                yield entity

        if self.export_info[0]:
            self.write_file.close()

    @staticmethod
    def extract_birth_date(line, title):
        """
        Matches a birth date from line using regex

        :param title: Name of entity
        :param line: String with wikipedia text from which birth date will be exported, if present
        """
        if "Joan Albert" in title:
            print("eee")

        if ("birth date" in line or "birth_date" in line or "birth-date" in line) and "infobox" in line:
            # birth is in format [1]year [2]month [3]day
            birth_date_match = re.search(
                "(?:birth date|birth date and age|birth-date|birth_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2})",
                line)
            if birth_date_match:
                return True, DateExport(int(birth_date_match[1]), int(birth_date_match[2]), int(birth_date_match[3]))


            # another format in infobox: birth-date|23 September 1996
            birth_date_match = re.search(
                "(?:birth date|birth-date|birth_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\W+(\d{1,2})(?: or?\W+\d{1,2})?\W+([a-zA-Z]+)\W+(\d{1,4})\s+(bc)?",
                line)
            if birth_date_match:
                try:
                    date = DateExport.from_format(birth_date_match[1] + " " + birth_date_match[2] + " " + birth_date_match[3], DateFormat.TXTMONTH_FULL)
                except:
                    pass
                else:
                    if birth_date_match[4] and "bc" in birth_date_match[4]:
                        date.BC = True
                    return True, date

            # another format in infobox: birth-date|September 23, 1996
            birth_date_match = re.search(
                "(?:birth date|birth-date|birth_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\W+([a-zA-Z]+)\W+(\d{1,2})(?: or?\W+\d{1,2})?\W+(\d{1,4})\s+(bc)?",
                line)
            if birth_date_match:
                try:
                    date = DateExport.from_format(birth_date_match[2] + " " + birth_date_match[1] + " " + birth_date_match[3], DateFormat.TXTMONTH_FULL)
                except:
                    pass
                else:
                    if birth_date_match[4] and "bc" in birth_date_match[4]:
                        date.BC = True
                    return True, date

            # another format in infobox: birth-date|c. 1750  or  birth-date|1950
            birth_date_match = re.search("(?:birth-date|birth_date|birth date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|(?:c.\W*)?([0-9]{1,4})", line)
            if birth_date_match:
                return True, DateExport.from_format(birth_date_match[1], DateFormat.YEAR_ONLY)

            # another format in infobox: birth-date|May, 1920
            birth_date_match = re.search("(?:birth-date|birth_date|birth date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n))?\|([a-zA-Z]+)(?:\W+|,)([0-9]{1,4})", line)
            if birth_date_match:
                return True, DateExport.from_format(birth_date_match[1] + " " + birth_date_match[2], DateFormat.TXTMONTH_AND_YEAR)

        # Another check if it is a person
        person_check = re.search("Category:[a-zA-Z\d\W]+(?:births|actors|actor|people|winner|winners|singers|singer|politician|deaths|photographers|artists|wrestlers|)", line)

        if person_check:
            # Try to find birth date in text
            # FORMAT: Name (names...) Surname (born Month DD, YYYY)
            birth_date_match = re.search("([a-zA-Z\W]*) born ([a-zA-Z]+ \d{1,2},\W*\d{4})", line)

            # Check if the title has something common with person's name in the .* previous content of the line
            person_name_split = title.split(' ')
            if birth_date_match and all(elem in birth_date_match[0] for elem in person_name_split):
                # export date
                print("some new match on", title)
                return True, DateExport.from_format(birth_date_match[2], DateFormat.AS_TEXT)


        return False, None

    @staticmethod
    def extract_death_date(line, title):
        """
        Matches a death date from line using regex

        :param title:
        :param line: String with wikipedia text from which death date will be exported, if present
        """
        if ("death date" in line or "death_date" in line or "death-date" in line)  and "infobox" in line:
            # death is in format [1]year [2]month [3]day
            death_date_match = re.search(
                "(?:death date|death date and age|death-date|death_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2})\s*\|",
                line)
            if death_date_match:
                return True, DateExport(int(death_date_match[1]), int(death_date_match[2]), int(death_date_match[3]))

            # another format in infobox: death-date|23 September 1996
            death_date_match = re.search(
                "(?:death date|death-date|death_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\W+(\d{1,2})(?: or?\W+\d{1,2})?\W+([a-zA-Z]+)\W+(\d{1,4})\s+(bc)?",
                line)
            if death_date_match:
                try:
                    date = DateExport.from_format(death_date_match[1] + " " + death_date_match[2] + " " + death_date_match[3],DateFormat.TXTMONTH_FULL)
                except:
                    pass
                else:
                    if death_date_match[4] and "bc" in death_date_match[4]:
                        date.BC = True

                    return True, date

            # another format in infobox: birth-date|September 23, 1996
            death_date_match = re.search(
                "(?:death date|death-date|death_date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\W+([a-zA-Z]+)\W+(\d{1,2})(?: or?\W+\d{1,2})?\W+(\d{1,4})\s+(bc)?",
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
            death_date_match = re.search("(?:death-date|death_date|death date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n)|\s+)?\|(?:c.\W*)?([0-9]{1,4})", line)
            if death_date_match:
                return True, DateExport.from_format(death_date_match[1], DateFormat.YEAR_ONLY)

            # another format in infobox: death-date|May, 1920  or  death_date|mf=yes|January,1205
            death_date_match = re.search("(?:death-date|death_date|death date)\W*(?:\|df=(?:yes|y|no|n)|\|mf=(?:yes|y|no|n))?\|([a-zA-Z]+)(?:\W+|,)([0-9]{1,4})", line)
            if death_date_match:
                return True, DateExport.from_format(death_date_match[1] + " " + death_date_match[2], DateFormat.TXTMONTH_AND_YEAR)

        return False, None
