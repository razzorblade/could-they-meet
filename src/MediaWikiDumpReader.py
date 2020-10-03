from lxml import etree
import re


class MediaWikiDumpReader:
    def __init__(self, file, gazeteers):
        # Prepend the default Namespace {*} to get anything.
        self.context = etree.iterparse(file, events=("end",), tag=['{*}page'])
        self.gazeteers = gazeteers

    def _start_parse(self):
        for event, element in self.context:
            yield event, element

            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]

    def __iter__(self):
        for event, elem in self._start_parse():
            entity = {}
            nsmap = {'x': 'http://www.mediawiki.org/xml/export-0.10/'}
            is_person = True

            for text in elem.xpath('//x:text', namespaces=nsmap):
                if not text.text:
                    continue

                is_person &= "|birth_date" in text.text or "| birth_date" in text.text or " birth_date" in text.text
                break

            for title in elem.xpath('//x:title', namespaces=nsmap):
                entity["title"] = title.text

                if not is_person:
                    # check if is person by using gazeteer
                    split_name = title.text.lower().split(' ')

                    if len(split_name) >= 2:
                        if split_name[0] in self.gazeteers["firstnames"] and split_name[len(split_name) - 1] in self.gazeteers["surenames"]:
                            is_person = True
                            # Find date

                break


            if is_person:
                entity['person'] = "1"
            else:
                entity['person'] = "0"

            yield entity
