from typing import List
import fitz  # PyMuPDF
import io
import requests
import os

class PDFProcessor:
    @staticmethod
    def download_pdf(url: str) -> bytes:
        response = requests.get(url)
        return response.content

    @staticmethod
    def extract_text(pdf_content: bytes) -> str:
        text = ""
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text

    @staticmethod
    def extract_text_from_file(pdf_path: str) -> str:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    @staticmethod
    def clean_text(text: str) -> str:
        # Remove extra whitespace and normalize text
        return " ".join(text.split()) 