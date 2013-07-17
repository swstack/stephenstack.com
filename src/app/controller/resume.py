from BeautifulSoup import BeautifulSoup
from StringIO import StringIO


class ResumeBuilder(object):
    def __init__(self, resource_manager):
        self._resource_manager = resource_manager
        self._docx_path = self._resource_manager.get_fs_resource_path("resume.docx")
        self._pdf_path = self._resource_manager.get_fs_resource_path("resume.pdf")
        self._html_path = self._resource_manager.get_fs_resource_path("resume.htm")

        # Will hold the HTML formatted resume
        self._resume = None

    #================================================================================
    # Start
    #================================================================================
    def start(self):
        pass

    #================================================================================
    # Private
    #================================================================================
    def _insert_divs(self, resume):
        section_ids_reversed = ["hobbies",
                                "experience",
                                "education",
                                "technical_skills",
                                "objective"]
        resume = StringIO(resume)
        h1s_encountered = 0
        final = "<div id='entire_resume'>"
        for line in resume.readlines():
            for word in line.split(" "):
                if word == "<h1" and section_ids_reversed != []:
                    if h1s_encountered == 0:
                        final += "<div id='%s'>" % section_ids_reversed.pop()
                        final += word + " "
                    else:
                        final += "</div"
                        final += "<div id='%s'>" % section_ids_reversed.pop()
                        final += word + " "
                    h1s_encountered += 1
                else:
                    final += word + " "
        final += "</div></div>"
        return final

    #================================================================================
    # Public
    #===============================================================================
    def get_resume(self):
        if not self._resume:
            raw = open(self._html_path).read()
            soup = BeautifulSoup(raw)
            soup_resume = soup.prettify()
            self._resume = self._insert_divs(soup_resume)
        return self._resume
