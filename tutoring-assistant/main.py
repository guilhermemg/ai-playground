import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from tutoring_system import TutoringSystem


QUESTIONNAIRE = """#####
Questionnaire:
    Q1: "What is the capital of France?"
    Q2: "Who wrote Hamlet?"
    Q3: "What is the formula for the area of a circle?"
    Q4: "What is the boiling point of water in Fahrenheit?"
    Q5: "Who discovered penicillin?"
    Q6: "What is the square root of 144?"
    Q7: "What is the chemical symbol for gold?"
    Q8: "Who painted the Mona Lisa?"
    Q9: "What is the largest planet in our solar system?"
    Q10: "Who is the author of 'To Kill a Mockingbird'?"

Student Answers:
    Q1: "Paris"
    Q2: "Shakespeare"
    Q3: "πr^2"
    Q4: "212 F"
    Q5: "Fleming"
    Q6: "13"
    Q7: "Ag"
    Q8: "Michelangelo"
    Q9: "Pluto"
    Q10: "Harper Lee"
######
"""


if __name__ == "__main__":
    print("Initializing Tutoring System...")
    tutor = TutoringSystem()

    print("Evaluating questionnaire...\n")
    result = tutor.evaluate_questionnaire(QUESTIONNAIRE)

    print("\n" + "=" * 50)
    print("EVALUATION RESULT")
    print("=" * 50)
    print(result)
