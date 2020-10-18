from lxml import etree
from date_export import DateExport
from runtime_constants import RuntimeConstants as Constants
import attr_type_constraint
import re
import html


@attr_type_constraint.auto_attr_check
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

    def _start_parse(self):
        for event, element in self.context:
            yield event, element

            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]

    def __iter__(self):

        if self.export_info[0]:
            write_file = open(self.export_info[1], "w", encoding="utf-8")

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
            for line in inner_page.splitlines():

                line = line.strip().lower()

                # Try to find birth and death dates in current line
                if not birth_date_found:
                    (birth_date_found, birth_date) = self.extract_birth_date(line)
                if not death_date_found:
                    (death_date_found, death_date) = self.extract_death_date(line)

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
                        birth_date_found = True

                # Update export_flag. We wont have to search for more, if both dates were found
                export_flag = birth_date_found and death_date_found
                if export_flag:
                    break

            if export_flag:
                if self.export_info[0]:
                    write_str = entity["name"] + "," + entity["birth_date"].__repr__() + "," + entity["death_date"].__repr__() + "\n"
                    # noinspection PyUnboundLocalVariable
                    write_file.write(write_str)
                yield entity

        if self.export_info[0]:
            write_file.close()

    @staticmethod
    def extract_birth_date(line):
        """
        Matches a birth date from line using regex

        :param line: String with wikipedia text from which birth date will be exported, if present
        """
        if "birth date" in line:
            # birth is in format [1]year [2]month [3]day
            birth_date_match = re.search("(?:birth date|birth date and age)(?:\|df=yes|\|mf=yes|\s+)?\|([0-9]{4})\|([0-9]{1,2})\|([0-9]{1,2})", line)

            if birth_date_match:
                return True, DateExport(int(birth_date_match[1]), int(birth_date_match[2]), int(birth_date_match[3]))

        return False, None

    @staticmethod
    def extract_death_date(line):
        """
        Matches a death date from line using regex

        :param line: String with wikipedia text from which death date will be exported, if present
        """
        if "death date" in line:
            # birth is in format [1]year [2]month [3]day
            death_date_match = re.search("(?:death date|death date and age)(?:\|df=yes|\|mf=yes|\s+)?\|([0-9]{4})\|([0-9]{1,2})\|([0-9]{1,2})\s*\|", line)

            if death_date_match:
                return True, DateExport(int(death_date_match[1]), int(death_date_match[2]), int(death_date_match[3]))

        return False, None
