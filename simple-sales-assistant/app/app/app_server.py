import json
import openai
import logging
import uvicorn

from fastapi import FastAPI
from base_models import UserInput, GenChatOutput
from base_models import FormattedChatOutput

import assit_utils as assist_utils


logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


app = FastAPI(title="Deploying My First LLM App", description="This is a simple app to deploy a LLM model", version="0.1.0")


def process_user_message(user_input, debug=True):
    delimiter = "```"

    # Step 0: Check if the user input is empty
    if user_input == "":
        if debug: logger.info("Step 0: User input is empty.")
        return "Hello! How can I assist you today? What specific product or information are you looking for?"

    if debug: logger.info("Step 0: User input is not empty.")
    
    # Step 1: Check input to see if it flags the Moderation API or is a prompt injection
    response = openai.Moderation.create(input=user_input)
    moderation_output = response["results"][0]

    if moderation_output["flagged"]:
        logger.info("Step 1: Input flagged by Moderation API.")
        return "Sorry, we cannot process this request."

    if debug: logger.info("Step 1: Input passed moderation check.")
    
    category_and_product_response = assist_utils.find_category_and_product_only(user_input, assist_utils.get_products_and_category())
    
    # Step 2: Extract the list of products
    category_and_product_list = assist_utils.read_string_to_list(category_and_product_response)
    
    if debug: logger.info("Step 2: Extracted list of products.")

    # Step 3: If products are found, look them up
    product_information = assist_utils.generate_output_string(category_and_product_list)
    if debug: logger.info("Step 3: Looked up product information.")

    # Step 4: Answer the user question
    system_message = f"""
    You are a customer service assistant for a large electronic store. \
    Respond in a friendly and helpful tone, with concise answers. \
    Make sure to ask the user relevant follow-up questions.
    """
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': f"{delimiter}{user_input}{delimiter}"},
        {'role': 'assistant', 'content': f"Relevant product information:\n{product_information}"}
    ]

    final_response = assist_utils.get_completion_from_messages(messages)
    if debug: logger.info("Step 4: Generated response to user question.")
    
    # Step 5: Put the answer through the Moderation API
    response = openai.Moderation.create(input=final_response)
    moderation_output = response["results"][0]

    if moderation_output["flagged"]:
        if debug: logger.info("Step 5: Response flagged by Moderation API.")
        return "Sorry, we cannot provide this information."

    if debug: logger.info("Step 5: Response passed moderation check.")

    # Step 6: Ask the model if the response answers the initial user query well
    user_message = f"""
    Customer message: {delimiter}{user_input}{delimiter}
    Agent response: {delimiter}{final_response}{delimiter}

    Does the response sufficiently answer the question?
    """
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    evaluation_response = assist_utils.get_completion_from_messages(messages)
    if debug: logger.info("Step 6: Model evaluated the response.")

    # Step 7: If yes, use this answer; if not, say that you will connect the user to a human
    if "Y" in evaluation_response:  # Using "in" instead of "==" to be safer for model output variation (e.g., "Y." or "Yes")
        if debug: logger.info("Step 7: Model approved the response.")
        return final_response
    else:
        if debug: logger.info("Step 7: Model disapproved the response.")
        neg_str = "I'm unable to provide the information you're looking for. I'll connect you with a human representative for further assistance."
        return neg_str


def process_user_message_2(user_input):
    response = assist_utils.find_category_and_product_v2(user_input)
    json_like_str = response.replace("'",'"')
    dicts_list = json.loads(json_like_str)
    output = {'assistance': dicts_list}
    return output


@app.post("/generic_assist_client")
def get_generic_assistance(u_input: UserInput):
    response = process_user_message(u_input.msg)
    return GenChatOutput(**{"assistance": response})


@app.post("/structured_assist_client")
def get_formatted_assistance(u_input: UserInput):
    response = process_user_message_2(u_input.msg)
    return FormattedChatOutput(**response)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

