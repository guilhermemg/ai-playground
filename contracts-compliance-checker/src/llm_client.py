import os
from dotenv import load_dotenv, find_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

from schemas.risk_schema import RiskExtractionOutput

# Load environment variables
load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the LLM
_llm = ChatOpenAI(
    temperature=0.0,
    model="gpt-3.5-turbo",
    api_key=OPENAI_API_KEY
)

# Set up the Pydantic output parser
_parser = PydanticOutputParser(pydantic_object=RiskExtractionOutput)


def call_llm(prompt: str) -> dict:
    """
    Call the LLM with the given prompt and return structured risk extraction output.
    
    Args:
        prompt: The formatted prompt containing the text to analyze
        
    Returns:
        dict: A dictionary with 'risks' key containing list of risk objects
    """
    # Create a prompt template that includes format instructions
    format_instructions = _parser.get_format_instructions()
    
    full_prompt = f"""{prompt}

{format_instructions}"""
    
    # Call the LLM
    response = _llm.invoke(full_prompt)
    
    # Parse the response into the Pydantic model
    parsed_output = _parser.parse(response.content)
    
    # Return as dict for compatibility with the pipeline
    return parsed_output.model_dump()
