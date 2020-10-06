from lxml import etree
import re
from xml.sax.saxutils import unescape, escape
import html


class MediaWikiDumpReader:

    def __init__(self, file, gazetteers):
        self.context = etree.iterparse(file, events=("end",), tag=['{*}page'])
        self.gazetteers = gazetteers

    def _start_parse(self):
        for event, element in self.context:
            yield event, element

            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]

    def __iter__(self):
        for event, elem in self._start_parse():
            entity = {}

            # Get inner text
            inner_page = etree.tostring(elem).decode("UTF-8")

            # Check if this page is a redirect to another page, therefore, processing will be skipped
            redirect_match = re.search("<redirect title=\"(.*)\"\/>", inner_page)
            if redirect_match:
                continue

            # Get title of this page
            exported_title = html.unescape(re.search("<title>([\s\S]*?)<\/title>", inner_page)[1])

            entity["name"] = exported_title

            # Basic check if infobox contains birth date
            is_person = "|birth_date" in inner_page or "| birth_date" in inner_page or " birth_date" in inner_page

            entity['person'] = "1" if is_person else "0"
            yield entity
