"""Single LLM Agent Text Reply Scenario.

This scenario uses pure Google ADK to create a simple math-answering agent.
It captures all ADK events generated during the conversation for use as fixtures.
"""

from google.adk.agents.llm_agent import LlmAgent
from runner_utils import run_simple_agent_scenario


async def run_scenario(collector) -> None:
    """Run the single LLM agent text reply scenario using pure Google ADK.

    We don't have streaming here, so it would be simple one event request->response."""

    # Create a simple ADK agent for basic math
    math_agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="math_assistant",
        instruction="You are a helpful math assistant. Answer math questions clearly and concisely."
    )
    
    # Use the common workflow function
    await run_simple_agent_scenario(
        agent=math_agent,
        user_message="What is 2+2?",
        collector=collector,
        app_name="math_test_app",
        user_id="test_user_001",
        session_id="test_session_001"
    )