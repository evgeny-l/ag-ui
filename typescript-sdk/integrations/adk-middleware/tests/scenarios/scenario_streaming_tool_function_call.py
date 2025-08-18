"""Streaming Tool Function Call Scenario.

This scenario demonstrates streaming LLM responses with function tool usage.
The agent is equipped with a simple math tool 'magic_with_two_numbers' that
performs addition. The user message explicitly requests using the tool to
force function calling behavior.
"""

import logging

from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import RunConfig
from google.adk.agents.run_config import StreamingMode
from runner_utils import run_in_memory_agent_scenario

logger = logging.getLogger(__name__)


def magic_with_two_numbers(first_number: int, second_number: int) -> int:
    """
    Performs magical mathematics by adding two numbers together.
    
    Args:
        first_number (int): The first magical number
        second_number (int): The second magical number
        
    Returns:
        int: The magical result of adding the two numbers
    """
    result = first_number + second_number
    logger.info(f"Magic tool called: {first_number} + {second_number} = {result}")
    return result


async def run_scenario(collector) -> None:
    """Run scenario testing streaming LLM responses with function tool usage."""
    
    logger.info("Testing streaming agent with function tool calling")

    # Create agent with the magic tool
    tool_agent = LlmAgent(
        name="MagicToolAgent",
        model="gemini-2.0-flash-exp",
        instruction="You are a magical math assistant. When asked to perform magic with numbers, use the magic_with_two_numbers tool. Always use the tool when explicitly requested.",
        description="Agent demonstrating function tool usage with streaming responses",
        tools=[magic_with_two_numbers]  # Add the tool to the agent
    )
    
    # Create RunConfig with streaming enabled
    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
    
    # Use in-memory runner workflow with streaming config
    await run_in_memory_agent_scenario(
        agent=tool_agent,
        user_message="Make magic via tool with 2 numbers: 5 and 10",
        collector=collector,
        app_name="tool_streaming_test_app",
        user_id="test_user_004",
        session_id="test_session_tools",
        run_config=run_config  # Enable streaming
    )