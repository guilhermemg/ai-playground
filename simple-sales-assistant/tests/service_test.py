
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
    

    def test_generic_assistance_1(self):
        resp = make_request(TargetURL.GENERIC_ASSISTANCE_URL, "I want to buy a phone")
        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("phone" in data["assistance"])
        self.assertTrue("brand" in data["assistance"])

    
    def test_generic_assistance_with_badwords(self):
        resp = make_request(TargetURL.GENERIC_ASSISTANCE_URL, "I want to hurt someone!")
        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["assistance"], "Sorry, we cannot process this request.")


    def test_structured_assistance_1(self):
        resp = make_request(TargetURL.FORMATTED_ASSISTANCE_URL, MSG_IDEAL_PAIR_SET[0]["customer_msg"])
        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        
        eval_score = eval_response_with_ideal(data["assistance"], MSG_IDEAL_PAIR_SET[0]["ideal_answer"])
        
        self.assertEqual(eval_score, 1.0)
    

    def test_structured_assistance_2(self):
        resp = make_request(TargetURL.FORMATTED_ASSISTANCE_URL, MSG_IDEAL_PAIR_SET[1]["customer_msg"])
        data = resp.json()
        self.assertEqual(resp.status_code, 200)

        eval_score = eval_response_with_ideal(data["assistance"], MSG_IDEAL_PAIR_SET[1]["ideal_answer"])

        self.assertEqual(eval_score, 0.0, "The response should be: " + str(MSG_IDEAL_PAIR_SET[1]["ideal_answer"]) + " but got: " + str(data["assistance"]))

    
    def test_structured_assistance_3(self):
        resp = make_request(TargetURL.FORMATTED_ASSISTANCE_URL, MSG_IDEAL_PAIR_SET[2]["customer_msg"])
        data = resp.json()
        self.assertEqual(resp.status_code, 200)

        eval_score = eval_response_with_ideal(data["assistance"], MSG_IDEAL_PAIR_SET[2]["ideal_answer"])

        self.assertEqual(eval_score, 1.0)

    
    def test_structured_assistance_overall_efficacy(self):
        """
        Test the overall efficacy of the assistant is greater than 0.8 (80%).
        """
        total_score = 0
        for i in range(len(MSG_IDEAL_PAIR_SET)):
            resp = make_request(TargetURL.FORMATTED_ASSISTANCE_URL, MSG_IDEAL_PAIR_SET[i]["customer_msg"])
            data = resp.json()
            eval_score = eval_response_with_ideal(data["assistance"], MSG_IDEAL_PAIR_SET[i]["ideal_answer"])
            total_score += eval_score
        avg_score = total_score / len(MSG_IDEAL_PAIR_SET)
        self.assertEqual(avg_score, 0.9, "The average score is: " + str(avg_score) + " which is less than 0.9")
