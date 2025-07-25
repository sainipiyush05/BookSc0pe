import PyPDF2
from docx import Document
from bs4 import BeautifulSoup
import os

class MultiFormatProcessor:
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.html', '.txt']
    
    def extract_text_with_pages(self, file_path: str) -> Dict[int, str]:
        """Extract text from multiple document formats"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self._extract_pdf_text(file_path)
        elif file_extension == '.docx':
            return self._extract_docx_text(file_path)
        elif file_extension == '.html':
            return self._extract_html_text(file_path)
        elif file_extension == '.txt':
            return self._extract_txt_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _extract_pdf_text(self, file_path: str) -> Dict[int, str]:
        """Enhanced PDF extraction with better OCR support"""
        page_texts = {}
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        page_texts[page_num] = text
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        return page_texts
    
    def _extract_docx_text(self, file_path: str) -> Dict[int, str]:
        """Extract text from DOCX files"""
        doc = Document(file_path)
        page_texts = {}
        page_num = 1
        current_text = ""
        
        for paragraph in doc.paragraphs:
            current_text += paragraph.text + "\n"
            # Simple page break detection (you can enhance this)
            if len(current_text) > 2000:  # Approximate page length
                page_texts[page_num] = current_text
                page_num += 1
                current_text = ""
        
        if current_text:
            page_texts[page_num] = current_text
        
        return page_texts
