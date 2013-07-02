from StringIO import StringIO


class _HTMLTag(object):
    """Encapsulation of a string HTML begin tag and it's content that follows
    the form:
            <tag>content

    The fact that the HTML tag has a closing tag is implied.
    """
    def __init__(self):
        self.name = ""
        self.content = ""

    def __repr__(self):
        return "<%s>%s</%s>" % (self.name, self.content, self.name)

    def _make_closing_tag(self):
        """Making a closing tag string for this ``HTMLTag`` object"""
        return "</%s>" % self.tagname

    def add_char_to_name(self, char):
        self.name += char

    def add_char_to_content(self, char):
        self.content += char


class XMLParser(object):
    """Custom XML parser, just for shits"""
    def __init__(self):
        self._string = None
        self._stringio = None

    #================================================================================
    # Private
    #================================================================================
    def _grab_next_char(self):
        return self._stringio.read(1)

    #================================================================================
    # Public Interface
    #================================================================================
    def parse(self, xml_string):
        self._string = xml_string
        self._stringio = StringIO(xml_string)
        tag_stack = []

        c = self._grab_next_char()
        while c != "":
            if c == "<":
                current_tag = _HTMLTag()
                while c != ">":
                    if c != ">" and c != "<":
                        current_tag.add_char_to_name(c)
                    c = self._grab_next_char()
                else:
                    c = self._grab_next_char()
                    while c != "<":  # while not the next tag
                        current_tag.add_char_to_content(c)
                    else:
                        continue
            c = self._grab_next_char()
        print tag_stack

    def parse2(self, xml_string):
        pass


if __name__ == "__main__":
    # Test
    example_xml = (
        "<html>"
            "<head>"
                "<title>My Title</title>"
            "</head>"
            "<body>"
                "<h1>Sup fool</h1>"
                "<p>Herrroooo</p>"
                "<table>"
                    "<tr>"
                        "<th>Col1 Header</th>"
                        "<th>Col2 Header</th>"
                    "</tr>"
                    "<tr>"
                        "<td>Col1 D1</td>"
                        "<td>Col2 D2</td>"
                    "</tr>"
                "</table>"
            "</body>"
        "</html"
    )

    xml_parser = XMLParser()
    xml_dict_repr = xml_parser.parse(example_xml)
    print xml_dict_repr
