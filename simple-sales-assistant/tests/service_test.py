
import unittest

from test_data import MSG_IDEAL_PAIR_SET
from test_utils import TargetURL, make_request
from test_utils import eval_response_with_ideal


class Test_API_ClientAssistant(unittest.TestCase):
    
    def test_greting(self):
        resp = make_request(TargetURL.GENERIC_ASSISTANCE_URL, "Hi")
        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["assistance"], "Hello! How can I assist you today?")
    

    def test_1(self):
        resp = make_request(TargetURL.FORMATTED_ASSISTANCE_URL, MSG_IDEAL_PAIR_SET[0]["customer_msg"])
        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        
        eval_score = eval_response_with_ideal(data["assistance"], MSG_IDEAL_PAIR_SET[0]["ideal_answer"])
        
        self.assertEqual(eval_score, 1.0)
    

    def test_2(self):
        resp = make_request(TargetURL.FORMATTED_ASSISTANCE_URL, MSG_IDEAL_PAIR_SET[1]["customer_msg"])
        data = resp.json()
        self.assertEqual(resp.status_code, 200)

        eval_score = eval_response_with_ideal(data["assistance"], MSG_IDEAL_PAIR_SET[1]["ideal_answer"])

        self.assertEqual(eval_score, 0.0, "The response should be: " + str(MSG_IDEAL_PAIR_SET[1]["ideal_answer"]) + " but got: " + str(data["assistance"]))

    
    def test_3(self):
        resp = make_request(TargetURL.FORMATTED_ASSISTANCE_URL, MSG_IDEAL_PAIR_SET[2]["customer_msg"])
        data = resp.json()
        self.assertEqual(resp.status_code, 200)

        eval_score = eval_response_with_ideal(data["assistance"], MSG_IDEAL_PAIR_SET[2]["ideal_answer"])

        self.assertEqual(eval_score, 1.0)
