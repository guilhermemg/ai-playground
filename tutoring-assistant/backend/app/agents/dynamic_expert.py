from __future__ import annotations

from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.outputs import LLMResult
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent

from app.agents.tools_registry import build_tools
from app.config.settings import get_settings
from app.observability.metrics import LLM_TOKENS_USED


class TokenCountCallback(BaseCallbackHandler):
    """Captures token usage from every LLM call inside an AgentExecutor."""

    def __init__(self, model: str):
        super().__init__()
        self.model = model
        self._input_tokens = 0
        self._output_tokens = 0

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        for generations in response.generations:
            for gen in generations:
                info = gen.generation_info or {}
                usage = info.get("usage_metadata") or info.get("token_usage") or {}
                self._input_tokens += usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
                self._output_tokens += usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)

        llm_output = response.llm_output or {}
        usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
        self._input_tokens += usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
        self._output_tokens += usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)

    def flush(self) -> None:
        if self._input_tokens:
            LLM_TOKENS_USED.labels(model=self.model, type="input").inc(self._input_tokens)
        if self._output_tokens:
            LLM_TOKENS_USED.labels(model=self.model, type="output").inc(self._output_tokens)


class DynamicExpertAgent:
    """A single agent class instantiated dynamically from database configuration.

    Each instance represents a domain expert (Medicine, Law, Physics, etc.)
    configured by the professor at runtime.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        domain: str,
        system_message: str,
        full_prompt: str,
        enabled_tools: list[str],
        retriever: Any | None = None,
        agent_namespace: str | None = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.domain = domain
        self.system_message = system_message
        self.full_prompt = full_prompt
        self.enabled_tools_names = enabled_tools

        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.0,
            api_key=settings.openai_api_key,
        )

        self.tools = build_tools(
            enabled_tools,
            retriever=retriever,
            agent_namespace=agent_namespace,
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        if self.tools:
            self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
            self.executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10,
                return_intermediate_steps=True,
            )
        else:
            self.executor = None

    def _record_token_usage(self, response) -> None:
        usage = getattr(response, "usage_metadata", None) or {}
        model = self.llm.model_name
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        if input_tokens:
            LLM_TOKENS_USED.labels(model=model, type="input").inc(input_tokens)
        if output_tokens:
            LLM_TOKENS_USED.labels(model=model, type="output").inc(output_tokens)

    def _record_executor_token_usage(self, result: dict) -> None:
        for step in result.get("intermediate_steps", []):
            messages = step[0].messages if hasattr(step[0], "messages") else []
            for msg in messages:
                self._record_token_usage(msg)
        llm_output = result.get("__raw_response__")
        if llm_output:
            self._record_token_usage(llm_output)

    async def ainvoke(self, question: str, answer: str) -> dict:
        input_text = self.full_prompt.replace("{question}", question).replace("{answer}", answer)

        if self.executor:
            cb = TokenCountCallback(self.llm.model_name)
            result = await self.executor.ainvoke(
                {"input": input_text},
                config={"callbacks": [cb]},
            )
            cb.flush()
            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "domain": self.domain,
                "output": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
            }

        response = await self.llm.ainvoke([
            SystemMessage(content=self.system_message),
            HumanMessage(content=input_text),
        ])
        self._record_token_usage(response)
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "domain": self.domain,
            "output": response.content,
            "intermediate_steps": [],
        }

    async def astream(self, question: str):
        """Stream response tokens for the chat interface."""
        input_text = f"Question: {question}"

        if self.executor:
            async for event in self.executor.astream_events(
                {"input": input_text}, version="v2"
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield chunk.content
        else:
            last_chunk = None
            async for chunk in self.llm.astream([
                SystemMessage(content=self.system_message),
                HumanMessage(content=input_text),
            ]):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
                last_chunk = chunk
            if last_chunk:
                self._record_token_usage(last_chunk)
