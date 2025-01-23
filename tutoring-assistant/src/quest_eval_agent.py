
from typing import Dict, Any

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool


from generic_agent import GenericAgent


class QuestionnaireEvaluatorAgent(GenericAgent):
    def __init__(self, llm):
        super().__init__(llm)


    def _analyze_answers(self, answer_data: str) -> str:
        """Analyzes individual answers for depth and quality"""
        prompt = PromptTemplate(
            input_variables=["answer_data"],
            template="""Analyze the following answer for depth, accuracy, and understanding:
            {answer_data}
            Provide detailed feedback on:
            1. Accuracy of concepts
            2. Depth of understanding
            3. Areas for improvement"""
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(answer_data=answer_data)


    def _generate_feedback(self, results_data: str) -> str:
        """Generates comprehensive feedback based on questionnaire results"""
        prompt = PromptTemplate(
            input_variables=["results"],
            template="""Based on the following questionnaire results:
            {results}
            
            Provide detailed feedback including:
            1. Overall performance analysis
            2. Specific strengths identified
            3. Areas needing improvement
            4. Suggested next steps for learning"""
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(results=results_data)


    def _evaluate_questionnaire(self, questionnaire) -> Dict[str, Any]:
        """Evaluates questionnaire responses and provides scoring"""
        prompt = PromptTemplate(
            input_variables=["questionnaire"],
            template="""Evaluate the following questionnaire responses:
            Questionnaire: {questionnaire}
            
            Return the answer as a json with two keys: 'feedback' and 'score'.
            """
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(questionnaire=questionnaire)


    def create_agent_executor(self):
        """Creates an agent specialized in evaluating questionnaires"""
        tools = [
            Tool(
                name="evaluate_questionnaire",
                func=self._evaluate_questionnaire,
                description="Evaluates questionnaire responses and provides scoring"
            ),
            Tool(
                name="analyze_answers",
                func=self._analyze_answers,
                description="Analyzes individual question responses for depth and accuracy"
            )
        ]

        tools += self.generic_tools

        prefix = """You are responsible for evaluating student questionnaires. Your role is to:
        1. Provide detailed feedback on questionnaire responses showing each question, answer and evaluation
        2. Explain why the answer is correct or incorrect
        3. Calculate scores based on the student answers
        
        The questionnaire content and the student answers are delimitted by #####.

        Provide detailed evaluation results, feedback and a final score calculated as a percentage.

        You have access to the following tools:"""
        
        suffix = """Questionnaire: {input}
        {agent_scratchpad}"""
        
        return self.create_agent(tools, prefix, suffix)