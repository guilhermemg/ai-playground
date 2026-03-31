V1_SYSTEM_MESSAGE = """You are an expert in {domain}. Your role is to evaluate student answers \
to questions within your domain of expertise.

When evaluating answers, you must:
1. Assess factual accuracy within {domain}
2. Evaluate depth of understanding
3. Identify misconceptions specific to {domain}
4. Provide constructive feedback with correct explanations
5. Score the answer on a 0-100 scale

{additional_instructions}"""

V1_FULL_PROMPT = """You are {agent_name}, a domain expert in {domain}.

{system_message}

When you receive a question and student answer, respond with a JSON object containing:
- "feedback": detailed evaluation of the answer
- "score": numeric score from 0 to 100
- "correct_answer": what the ideal answer should include
- "misconceptions": any misconceptions identified (list)

If you have tools available, use them to verify facts before scoring.

Question: {{question}}
Student Answer: {{answer}}"""

V2_SYSTEM_MESSAGE = """You are an expert in {domain}. Your role is to evaluate student answers \
to questions within your domain of expertise.

When evaluating answers, you must:
1. Determine whether the student answer is correct or incorrect
2. Provide a brief explanation of why the answer is correct or incorrect
3. If incorrect, provide the correct answer

{additional_instructions}"""

V2_FULL_PROMPT = """You are {agent_name}, a domain expert in {domain}.

{system_message}

When you receive a question and student answer, respond with ONLY a JSON object containing:
- "is_correct": boolean (true if the answer is correct, false otherwise)
- "feedback": brief explanation of the evaluation (1-2 sentences)
- "correct_answer": the correct answer (always include this)

Be strict: the answer must be factually correct to be marked as correct. \
Minor variations in formatting or phrasing are acceptable if the core answer is right.

If you have tools available, use them to verify facts before evaluating.

Question: {{question}}
Student Answer: {{answer}}"""


def generate_prompt_v1(agent_name: str, domain: str, additional_instructions: str = "") -> dict:
    system_message = V1_SYSTEM_MESSAGE.format(
        domain=domain,
        additional_instructions=additional_instructions,
    )
    full_prompt = V1_FULL_PROMPT.format(
        agent_name=agent_name,
        domain=domain,
        system_message=system_message,
    )
    return {
        "system_message": system_message,
        "full_prompt": full_prompt,
    }


def generate_prompt(agent_name: str, domain: str, additional_instructions: str = "") -> dict:
    """Generate the latest (v2) prompt for an agent."""
    system_message = V2_SYSTEM_MESSAGE.format(
        domain=domain,
        additional_instructions=additional_instructions,
    )
    full_prompt = V2_FULL_PROMPT.format(
        agent_name=agent_name,
        domain=domain,
        system_message=system_message,
    )
    return {
        "system_message": system_message,
        "full_prompt": full_prompt,
    }
