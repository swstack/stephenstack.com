from BeautifulSoup import BeautifulSoup
from StringIO import StringIO
from docx import getdocumenttext, opendocx
from pdfminer.converter import TextConverter, HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, \
    PDFTextExtractionNotAllowed, process_pdf
from pdfminer.pdfparser import PDFParser, PDFDocument
from util.paths import HTTP_STATIC
import os


class ResumeBuilder(object):
    def __init__(self):
        self._pdf_path = None
        self._docx_path = None
        self._docx_resume = None
        self._paratextlist = None
        self._pdf_resume = None
        self._html_path = None

    @property
    def _resume(self):
        if not self._docx_resume:
            self._docx_resume = \
                opendocx(os.path.join(HTTP_STATIC, "Stack_Stephen_Resume_5_17_2013.docx"))
            self._paratextlist = getdocumenttext(self._docx_resume)
        return self._docx_resume

    def _dfs(self, treenode):
        children = treenode.getchildren()
        for child in children:
            print child.text
            self._dfs(child)

    def start(self):
#        self._docx_path = os.path.join(HTTP_STATIC, "Stack_Stephen_Resume_5_17_2013.docx")
        self._pdf_path = os.path.join(HTTP_STATIC, "Stack_Stephen_Resume_5_22_2013.pdf")
        self._html_path = os.path.join(HTTP_STATIC, "Stack_Stephen_Resume_5_22_2013.htm")

    def get_docx_resume(self):
        root = self._resume
        self._dfs(root)

    def get_pdf_resume(self, password=""):
        """Return html"""
        if not self._pdf_resume:
            rsrcmgr = PDFResourceManager()
            retstr = StringIO()
            codec = 'utf-8'
            laparams = LAParams()
            device = HTMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

            fp = file(self._pdf_path, 'rb')
            process_pdf(rsrcmgr, device, fp)
            fp.close()
            device.close()

            self._pdf_resume = retstr.getvalue()
            retstr.close()
        soup = BeautifulSoup(self._pdf_resume)
        return soup.prettify()

    def get_html_resume(self):
        """Return html"""
        raw = open(self._html_path).read()
        soup = BeautifulSoup(raw)
        return soup.prettify()
