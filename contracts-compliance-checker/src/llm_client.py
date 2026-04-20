import os
from typing import Optional

from dotenv import load_dotenv, find_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

from schemas.risk_schema import RiskExtractionOutput

# Set up the Pydantic output parser (no API key required)
_parser = PydanticOutputParser(pydantic_object=RiskExtractionOutput)

_llm: Optional[ChatOpenAI] = None


def _get_llm() -> ChatOpenAI:
    """Lazily construct the chat model so imports work without OPENAI_API_KEY (e.g. in tests)."""
    global _llm
    if _llm is None:
        load_dotenv(find_dotenv())
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env-template to .env and add your key."
            )
        _llm = ChatOpenAI(
            temperature=0.0,
            model="gpt-3.5-turbo",
            api_key=api_key,
        )
    return _llm


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
    response = _get_llm().invoke(full_prompt)
    
    # Parse the response into the Pydantic model
    parsed_output = _parser.parse(response.content)
    
    # Return as dict for compatibility with the pipeline
    return parsed_output.model_dump()
