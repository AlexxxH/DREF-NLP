"""
DREF Document Class
"""
import io
import requests
from functools import cached_property

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTImage, LTFigure, LTTextBox, LTTextBoxHorizontal

from dref_parsing import utils


class AppealDocument:
    """
    Parameters
    ----------
    """
    def __init__(self, created_at, document, document_url, appeal, document_type, iso, description, id, name, translation_module_original_language):

        # Set attributes from params
        self.created_at = created_at
        self.document = document
        self.document_url = document_url
        self.appeal = appeal
        self.document_type = document_type
        self.iso = iso
        self.description = description
        self.id = id
        self.name = name
        self.translation_module_original_language = translation_module_original_language

        # Get content
        pdf_data = requests.get(self.document_url).content
        self.content = io.BytesIO(pdf_data)

        # Get headers, footers, and postheaders
        self.headers, self.footers, self.postheaders = self.get_headers_footers_postheaders()


    def get_headers_footers_postheaders(self):
        """
        Get headers, footers, and postheaders from the document.
        """
        headers = []
        footers = []
        postheaders = []

        # Loop through pages
        for page_layout in extract_pages(self.content):
            postheader_now = False
            header_now = True
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    if utils.strip_all_empty(element.get_text()) != '':
                        element_text = element.get_text()

                        if postheader_now:
                            postheader = element_text
                            postheader_now = False

                        if header_now:
                            header = element_text
                            header_now = False
                            postheader_now = True

            headers.append(header)
            postheaders.append(postheader)
            footers.append(element_text)

        return headers, footers, postheaders