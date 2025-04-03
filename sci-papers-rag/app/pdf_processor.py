import fitz  # PyMuPDF
import re

class PDFProcessor:
    @staticmethod
    def extract_text_from_file(pdf_path: str) -> str:
        """Extract text from a PDF file using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            raise

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extracted text by removing extra whitespace, unwanted characters, and references section"""
        # Find the references/bibliography section
        reference_patterns = [
            r'\nReferences\s*\n',
            r'\nBibliography\s*\n',
            r'\nWorks Cited\s*\n',
            r'\nCitations\s*\n'
        ]
        
        # Find the first occurrence of references section
        ref_index = float('inf')
        for pattern in reference_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.start() < ref_index:
                ref_index = match.start()
        
        # Remove everything after references if found
        if ref_index != float('inf'):
            text = text[:ref_index]
        
        # Remove multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        # Remove form feed characters
        text = text.replace('\f', '')
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove citation patterns like [1], [2,3], etc.
        text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
        
        # Remove common citation patterns like (Author et al., 2023)
        text = re.sub(r'\([A-Za-z\s]+(?:et al\.)?(?:,\s*\d{4})*\)', '', text)
        
        return text.strip() 