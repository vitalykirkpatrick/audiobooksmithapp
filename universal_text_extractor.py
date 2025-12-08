"""
Universal Text Extractor
Extracts text from multiple ebook formats:
- PDF, EPUB, DOCX, TXT, RTF, MOBI, AZW, AZW3, ODT
"""

import os
import re


class UniversalTextExtractor:
    """Extract text from various ebook formats"""
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': self._extract_from_pdf,
            '.epub': self._extract_from_epub,
            '.docx': self._extract_from_docx,
            '.doc': self._extract_from_doc,
            '.txt': self._extract_from_txt,
            '.rtf': self._extract_from_rtf,
            '.mobi': self._extract_from_mobi,
            '.azw': self._extract_from_mobi,
            '.azw3': self._extract_from_mobi,
            '.odt': self._extract_from_odt
        }
    
    def extract_text(self, file_path):
        """Extract text from file based on extension"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Extract text using appropriate method
        extractor = self.supported_formats[ext]
        text = extractor(file_path)
        
        # Clean up text
        text = self._clean_text(text)
        
        return text
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF"""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def _extract_from_epub(self, file_path):
        """Extract text from EPUB"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            book = epub.read_epub(file_path)
            text = ""
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text += soup.get_text() + "\n"
            
            return text
        except Exception as e:
            raise Exception(f"EPUB extraction failed: {str(e)}")
    
    def _extract_from_docx(self, file_path):
        """Extract text from DOCX"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")
    
    def _extract_from_doc(self, file_path):
        """Extract text from DOC (legacy Word format)"""
        try:
            # Try using textract if available
            import textract
            text = textract.process(file_path).decode('utf-8')
            return text
        except:
            # Fallback: suggest converting to DOCX
            raise Exception("DOC format requires conversion. Please save as DOCX and upload again.")
    
    def _extract_from_txt(self, file_path):
        """Extract text from TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except:
                    continue
            raise Exception("Unable to decode text file. Please ensure it's UTF-8 encoded.")
    
    def _extract_from_rtf(self, file_path):
        """Extract text from RTF"""
        try:
            from striprtf.striprtf import rtf_to_text
            with open(file_path, 'r', encoding='utf-8') as file:
                rtf_content = file.read()
            return rtf_to_text(rtf_content)
        except Exception as e:
            raise Exception(f"RTF extraction failed: {str(e)}")
    
    def _extract_from_mobi(self, file_path):
        """Extract text from MOBI/AZW/AZW3"""
        try:
            import mobi
            tempdir, filepath = mobi.extract(file_path)
            
            # Read extracted HTML files
            from bs4 import BeautifulSoup
            text = ""
            
            for root, dirs, files in os.walk(tempdir):
                for file in files:
                    if file.endswith('.html'):
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            soup = BeautifulSoup(f.read(), 'html.parser')
                            text += soup.get_text() + "\n"
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(tempdir, ignore_errors=True)
            
            return text
        except Exception as e:
            raise Exception(f"MOBI/AZW extraction failed: {str(e)}")
    
    def _extract_from_odt(self, file_path):
        """Extract text from ODT (OpenDocument Text)"""
        try:
            from odf import text, teletype
            from odf.opendocument import load
            
            doc = load(file_path)
            all_text = ""
            
            for paragraph in doc.getElementsByType(text.P):
                all_text += teletype.extractText(paragraph) + "\n"
            
            return all_text
        except Exception as e:
            raise Exception(f"ODT extraction failed: {str(e)}")
    
    def _clean_text(self, text):
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if char == '\n' or char == '\t' or not char.isspace() or char == ' ')
        
        return text.strip()


if __name__ == "__main__":
    # Test the extractor
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        extractor = UniversalTextExtractor()
        try:
            text = extractor.extract_text(file_path)
            print(f"✅ Extracted {len(text)} characters")
            print(f"📝 First 500 characters:\n{text[:500]}")
        except Exception as e:
            print(f"❌ Error: {e}")
