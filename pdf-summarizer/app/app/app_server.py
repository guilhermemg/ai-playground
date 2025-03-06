import io
import os

import logging
import uvicorn

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from pdf_summarizer import extract_text_from_pdf

from dotenv import load_dotenv
load_dotenv()


logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


# Initialize LLM (GPT-3 or GPT-4)
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Define a prompt template for summarization
summary_prompt = "Summarize the following text:\n\n{text}"
prompt = PromptTemplate(input_variables=["text"], template=summary_prompt)

# Create a LangChain pipeline for summarization
chain = LLMChain(llm=llm, prompt=prompt)


def summarize_text(text):
    summary = chain.run(text)
    return summary


app = FastAPI(title="Deploying PDF Summarizer App", description="Summarize PDFs using GPT-3 or GPT-4")


class Document(BaseModel):
    title: str
    content: str


@app.post("/summarize/")
async def summarize_file(file: UploadFile = File(...)):
    contents = await file.read()
    text = extract_text_from_pdf(io.BytesIO(contents))  # Convert file to a file-like object
    summary = summarize_text(text)  # Generate summary
    return {"title": file.filename, "summary": summary}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")