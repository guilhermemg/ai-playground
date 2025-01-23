
from langchain.chains import LLMChain
from langchain.tools import Tool
from langchain.prompts import PromptTemplate


from generic_agent import GenericAgent


class TeachingMethodologistAgent(GenericAgent):
    def __init__(self, llm):
        super().__init__(llm)

        
    def _suggest_learning_strategy(self, context: str) -> str:
        """Suggests personalized learning strategies"""
        prompt = PromptTemplate(
            input_variables=["context"],
            template="Suggest effective learning strategies for this situation: {context}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(context=context)

    def _create_practice_exercise(self, topic: str) -> str:
        """Creates customized practice exercises"""
        prompt = PromptTemplate(
            input_variables=["topic"],
            template="Create a practice exercise for the following topic: {topic}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(topic=topic)
    
    def create_agent_executor(self):
        """Creates an agent specialized in teaching methods"""
        tools = [
            Tool(
                name="suggest_learning_strategy",
                func=self._suggest_learning_strategy,
                description="Suggests effective learning strategies"
            ),
            Tool(
                name="create_practice_exercise",
                func=self._create_practice_exercise,
                description="Creates tailored practice exercises"
            )
        ]
        
        prefix = """You are an expert in teaching methodology. Your role is to:
        1. Suggest effective learning strategies
        2. Create appropriate practice exercises
        3. Adapt teaching methods to student needs
        4. Provide constructive feedback
        
        You have access to the following tools:"""
        
        suffix = """Question: {input}
        {agent_scratchpad}"""
        
        return self.create_agent(tools, prefix, suffix)