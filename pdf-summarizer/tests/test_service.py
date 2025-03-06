import unittest

from test_utils import TargetURL, make_request


class Test_API_PDFSummarizer(unittest.TestCase):
    
    def test_1(self):
        resp = make_request(TargetURL.SUMMARIZE_PDF_URL, "./tests/data/resume.pdf")
               
        data = resp.json()
        
        print(data)
        
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("title" in data)
        self.assertTrue("summary" in data)
        
