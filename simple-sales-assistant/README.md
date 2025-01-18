
# Simple Sales Assistant

The **Simple Sales Assistant** is a microservice designed to be a sales assistant by leveraging OpenAI's API. It offers two types of responses:

1. **Generic Response**: A standard reply to client inquiries.
2. **Structured Response**: A JSON-formatted response, categorizing products by their types.

This project is part of the [AI Playground](https://github.com/guilhermemg/ai-playground/), a collection of AI experiments showcasing the power of language models, agents, and LangChain.

---

## Features

- **OpenAI Integration**: Utilizes OpenAI's API to generate relevant responses.
- **Dockerized Microservice**: Encapsulated in a Docker container for easy deployment.
- **Endpoints**:
  - **Generic Assistance**: Returns a simple response.
  - **Structured Assistance**: Returns a JSON-formatted response with categorized products.
- **Efficacy Testing**: Includes tests written with `unittest` to evaluate the system against ideal answers.
  - **Note**: The tests require the microservice to be running.

---

## Getting Started

### Prerequisites

- **Docker**: Ensure Docker is installed on your system.
- **OpenAI API Key**: Obtain an API key from OpenAI.

### Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/guilhermemg/ai-playground.git
   cd ai-playground/simple-sales-assistant
   ```

2. **Set Up Environment Variables**:

   Create a `.env` file in the project directory with the following content:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Build and Run the Docker Container**:

   ```bash
   docker build -t simple-sales-assistant .
   docker run -d -p 8000:8000 --env-file .env simple-sales-assistant
   ```

---

## Endpoints and Usage

### Generic Assistance Endpoint

- **Endpoint**: `/generic_assist_client`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "query": "I need help finding a good laptop."
  }
  ```
- **Response**:
  ```json
  {
    "assistance": "We recommend checking out our TechPro Ultrabook or BlueWave Gaming Laptop."
  }
  ```

### Structured Assistance Endpoint

- **Endpoint**: `/structured_assist_client`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "query": "Tell me about laptops in your store."
  }
  ```
- **Response**:
  ```json
  {
    "assistance": [
      {
        "category": "Computers and Laptops",
        "products": [
          "TechPro Ultrabook",
          "BlueWave Gaming Laptop",
          "PowerLite Convertible"
        ]
      }
    ]
  }
  ```

---

## Testing

The project includes tests written with the `unittest` framework. Ensure the microservice is running before executing the tests.

### Run Tests:
```bash
python -m unittest discover tests
```

---

*This project is part of the [AI Playground](https://github.com/guilhermemg/ai-playground/), showcasing various AI experiments and applications.*