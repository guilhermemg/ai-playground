import requests

from enum import Enum


class TargetURL(Enum):
    SUMMARIZE_PDF_URL = "http://localhost:8002/summarize"
    

def make_request(target_url: TargetURL, pdf_file_path: str):
    files = {"file": pdf_file_path}
    response = requests.post(target_url.value, files=files)
    return response