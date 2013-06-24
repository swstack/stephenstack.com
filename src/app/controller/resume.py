from BeautifulSoup import BeautifulSoup
from StringIO import StringIO
from pdfminer.converter import HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, process_pdf


class ResumeBuilder(object):
    def __init__(self, resource_manager):
        self._resource_manager = resource_manager
        self._docx_path = self._resource_manager.get_fs_resource_path("resume.docx")
        self._pdf_path = self._resource_manager.get_fs_resource_path("resume.pdf")

        # Will hold the HTML formatted resume
        self._resume = None

    def start(self):
        pass

    def get_resume(self):
        if not self._resume:
            rsrcmgr = PDFResourceManager()
            retstr = StringIO()
            codec = 'utf-8'
            laparams = LAParams()
            device = HTMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

            fp = file(self._pdf_path, 'rb')
            process_pdf(rsrcmgr, device, fp)
            fp.close()
            device.close()

            soup = BeautifulSoup(retstr.getvalue())
            retstr.close()
            self._resume = soup.prettify()
        return self._resume
