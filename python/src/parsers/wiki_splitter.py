from lxml import etree
import io


class MediaWikiDumpSplitter:

    def __init__(self, file_in, file_out, size):
        self.file_in = file_in
        self.file_out = file_out
        self.goal_size = size
        self._in_file_stream = open(self.file_in, "rb")
        self._out_file_stream = io.open(self.file_out, "w", encoding="utf-8")
        self.context = etree.iterparse(self._in_file_stream, events=("end",), tag=['{*}page'])

    def export_chunk(self):
        self._out_file_stream.write("<pages>")
        current_size = 0
        for event, element in self.context:

            inner_page = etree.tostring(element).decode("UTF-8")
            current_size += len(inner_page)
            if current_size > self.goal_size:
                break

            for line in inner_page.splitlines():
                self._out_file_stream.write(line)

            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]

        self._out_file_stream.write("</pages>")
        self._in_file_stream.close()
        self._out_file_stream.close()

