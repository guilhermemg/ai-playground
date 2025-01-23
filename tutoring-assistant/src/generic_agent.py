
from typing import List

from langchain.agents import load_tools
from langchain.agents import ZeroShotAgent, Tool, ZeroShotAgent, AgentExecutor
from langchain.chains import LLMChain


class GenericAgent:
    def __init__(self, llm):
        self.llm = llm

        self.generic_tools = load_tools(['llm-math','wikipedia'], llm=self.llm)
        
        
    def create_agent(self, tools: List[Tool], prefix: str, suffix: str):
        """Helper function to create an agent with specified tools and prompt"""
        prompt = ZeroShotAgent.create_prompt(
            tools,
            prefix=prefix,
            suffix=suffix,
            input_variables=["input", "agent_scratchpad"]
        )
        
        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        
        agent = ZeroShotAgent(
            llm_chain=llm_chain,
            tools=tools,
            verbose=True
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True
        )