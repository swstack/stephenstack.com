from BeautifulSoup import BeautifulSoup


class ResumeBuilder(object):
    def __init__(self, resource_manager):
        self._resource_manager = resource_manager
        self._docx_path = self._resource_manager.get_fs_resource_path("resume.docx")
        self._pdf_path = self._resource_manager.get_fs_resource_path("resume.pdf")
        self._html_path = self._resource_manager.get_fs_resource_path("resume.htm")

        # Will hold the HTML formatted resume
        self._resume = None

    def start(self):
        pass

    def get_resume(self):
        if not self._resume:
            raw = open(self._html_path).read()
            soup = BeautifulSoup(raw)
            self._resume = soup.prettify()
        return self._resume
