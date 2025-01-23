from langchain.chat_models import ChatOpenAI
from typing import Dict, Any

import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

import warnings
warnings.filterwarnings("ignore")


from subj_expert_agent import SubjectExpertAgent
from teach_method_agent import TeachingMethodologistAgent
from progress_tracker_agent import ProgressTrackerAgent
from quest_eval_agent import QuestionnaireEvaluatorAgent


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class TutoringSystem:
    def __init__(self):
        # Initialize the LLM with gpt-3.5-turbo
        self.llm = ChatOpenAI(
            temperature=0.0,
            model_name="gpt-3.5-turbo",  # Updated model
            openai_api_key=OPENAI_API_KEY
        )

        #self.questionnaire_results = {}
        
        # Initialize specialized agents
        #self.subject_expert_agent = SubjectExpertAgent(self.llm)
        #self.teaching_methodologist_agent = TeachingMethodologistAgent(self.llm)
        #self.progress_tracker_agent = ProgressTrackerAgent(self.llm)
        self.questionnaire_evaluator_agent = QuestionnaireEvaluatorAgent(self.llm)

        # Create agent executors
        #self.subject_expert = self.subject_expert_agent.create_agent_executor()
        #self.teaching_methodologist = self.teaching_methodologist_agent.create_agent_executor()
        #self.progress_tracker = self.progress_tracker_agent.create_agent_executor()
        self.questionnaire_evaluator = self.questionnaire_evaluator_agent.create_agent_executor()
                

    # public methods -----------------------------------------------------------

    def evaluate_questionnaire(self, questionnaire: str) -> Dict[str, Any]:
        """Public method to evaluate a questionnaire"""
        
        # Get detailed feedback
        evaluation = self.questionnaire_evaluator.run(
            f"""Generate comprehensive feedback for this questionnaire {questionnaire}. 
            
            The questionnaire and the student answers are delimitted by #####.

            Provide detailed evaluation results, feedback and a final score calculated as a percentage."""
        )
        
        return evaluation

    
    # def tutor(self, user_input: str, questionaire: str) -> str:
    #     """Main method to handle tutoring interactions"""
    #     # First, analyze the input with the teaching methodologist
    #     teaching_response = self.teaching_methodologist.run(
    #         f"""Analyze the following student input and suggest appropriate teaching approach: {user_input}.
    #          The student is supposed to answer the following test questions: {questionaire}."""
    #     )
        
    #     # Then, get subject matter expertise
    #     expert_response = self.subject_expert.run(
    #         f"""Address the following learning need: {user_input}\nTeaching context: {teaching_response}. 
    #         Do not show the student this response."""
    #     )
        
    #     # Finally, track progress
    #     progress_response = self.progress_tracker.run(
    #         f"""Track progress for:\nStudent input: {user_input}\nExpert response: {expert_response}.
    #         Track the student progress based on the number of questions solved from the questionaire."""
    #     )
        
    #     return f"Expert Response: {expert_response}\n\nLearning Strategy: {teaching_response}\n\nProgress Notes: {progress_response}"

    