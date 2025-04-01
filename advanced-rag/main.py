from dotenv import load_dotenv

load_dotenv()

from graph.graph import app

if __name__ == "__main__":
    print("Hello Advanced RAG")
    response = app.invoke(input={"question": "What is agent memory in a single sentence?"})

    print('Question:', response["question"])
    print('Generation:', response["generation"])
    print('Web Search:', response["web_search"])
    print('Total documents:', len(response["documents"]))