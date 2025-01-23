
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from generic_agent import GenericAgent


class SubjectExpertAgent(GenericAgent):
    def __init__(self, llm):
        super().__init__(llm)

    def _explain_concept(self, concept: str) -> str:
        """Provides detailed explanation of academic concepts"""
        prompt = PromptTemplate(
            input_variables=["concept"],
            template="Explain the following concept in detail: {concept}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(concept=concept)

    def _provide_examples(self, concept: str) -> str:
        """Generates relevant examples for concepts"""
        prompt = PromptTemplate(
            input_variables=["concept"],
            template="Provide practical examples for: {concept}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(concept=concept)

    def create_agent_executor(self):
        """Creates an agent specialized in subject matter expertise"""
        tools = [
            Tool(
                name="explain_concept",
                func=self._explain_concept,
                description="Explains academic concepts in detail"
            ),
            Tool(
                name="provide_examples",
                func=self._provide_examples,
                description="Provides relevant examples for concepts"
            )
        ]
        
        prefix = """You are an expert in academic subjects. Your role is to:
        1. Explain concepts clearly and accurately
        2. Provide detailed examples
        3. Answer subject-specific questions
        4. Identify and correct misconceptions
        
        You have access to the following tools:"""
        
        suffix = """Question: {input}
        {agent_scratchpad}"""

        return self.create_agent(tools, prefix, suffix)