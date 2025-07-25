import PyPDF2
import re
from typing import Dict, List

class PDFExtractor:
    def __init__(self):
        pass
    
    def extract_text_with_pages(self, pdf_path: str) -> Dict[int, str]:
        page_texts = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        page_texts[page_num] = text
                        
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            
        return page_texts
    
    def extract_metadata(self, pdf_path: str) -> Dict:
        metadata = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'total_pages': len(pdf_reader.pages)
                    }
                else:
                    metadata = {'total_pages': len(pdf_reader.pages)}
                    
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            
        return metadata
