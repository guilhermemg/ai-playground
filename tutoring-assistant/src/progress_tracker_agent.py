
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.tools import Tool


from generic_agent import GenericAgent


class ProgressTrackerAgent(GenericAgent):
    def __init__(self, llm):
        super().__init__(llm)

    def _track_progress(self, student_work: str) -> str:
        """Analyzes student progress"""
        prompt = PromptTemplate(
            input_variables=["student_work"],
            template="Analyze the following student work and provide progress insights: {student_work}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(student_work=student_work)

    def _generate_report(self, student_data: str) -> str:
        """Generates progress reports"""
        prompt = PromptTemplate(
            input_variables=["student_data"],
            template="Generate a detailed progress report based on: {student_data}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(student_data=student_data)
    
    def create_agent_executor(self):
        """Creates an agent for tracking student progress"""
        tools = [
            Tool(
                name="track_progress",
                func=self._track_progress,
                description="Tracks and analyzes student progress"
            ),
            Tool(
                name="generate_report",
                func=self._generate_report,
                description="Generates progress reports"
            ),
            
        ]
        
        prefix = """You are responsible for tracking student progress. Your role is to:
        1. Monitor learning progress
        2. Identify areas needing improvement
        3. Generate progress reports
        4. Suggest next learning steps
        
        You have access to the following tools:"""
        
        suffix = """Question: {input}
        {agent_scratchpad}"""
        
        return self.create_agent(tools, prefix, suffix)