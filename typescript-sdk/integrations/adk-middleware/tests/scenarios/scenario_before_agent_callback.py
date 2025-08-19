"""Before Agent Callback Scenario.

This scenario demonstrates using before_agent_callback to skip agent execution
based on session state. The callback returns a direct response instead of
letting the LLM agent process the message.
"""

from typing import Optional

from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from runner_utils import run_in_memory_agent_scenario


def check_if_agent_should_run(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback function that checks 'skip_llm_agent' in session state.
    This test scenario expects the skip condition to be True.
    """
    if callback_context.state.get("skip_llm_agent", False):
        return types.Content(
            parts=[types.Part(text=f"Skipped by before_agent_callback due to state condition.")],
            role="model"  # Assign model role to the overriding response
        )
    else:
        raise ValueError("Test scenario misconfigured: expected 'skip_llm_agent' to be True in session state")


async def run_scenario(collector) -> None:
    """Run the before agent callback scenario using pure Google ADK."""

    # Create an ADK agent with before_agent_callback
    controlled_agent = LlmAgent(
        name="ControlledAgent",
        model="gemini-2.0-flash-exp",
        instruction="You are a helpful assistant that should not be reached in this test.",
        description="An LLM agent demonstrating before_agent_callback",
        before_agent_callback=check_if_agent_should_run
    )
    
    # Use the common workflow function with state that will trigger the callback
    await run_in_memory_agent_scenario(
        agent=controlled_agent,
        user_message="This message should be intercepted by the callback.",
        collector=collector,
        app_name="callback_test_app",
        user_id="test_user_002",
        session_id="test_session_skip",
        session_state={"skip_llm_agent": True}  # This will trigger the callback
    )