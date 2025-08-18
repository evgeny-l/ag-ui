"""Streaming Message with States Scenario.

This scenario demonstrates streaming LLM responses with both before_agent_callback 
and after_agent_callback updating session state. The before callback adds a 
processing step, the agent streams a predictable counting response, and the 
after callback marks completion. This generates multiple events showing the 
full streaming callback lifecycle.
"""

import logging
from typing import Optional

from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.runners import RunConfig
from google.adk.agents.run_config import StreamingMode
from runner_utils import run_in_memory_agent_scenario

logger = logging.getLogger(__name__)


def before_callback_update_state(callback_context: CallbackContext) -> Optional[types.Content]:
    """Before callback that updates processing_step in session state."""
    logger.info("Before callback: Updating processing_step to 'started'")
    callback_context.state.update({"processing_step": "started"})
    # Return None to allow agent execution to continue
    return None


def after_callback_update_state(callback_context: CallbackContext) -> Optional[types.Content]:
    """After callback that updates processing_step in session state."""
    logger.info("After callback: Updating processing_step to 'completed'")
    callback_context.state.update({"processing_step": "completed"})
    # Return None to use the agent's original output
    return None


async def run_scenario(collector) -> None:
    """Run scenario testing both before and after agent callbacks updating state with streaming."""
    
    logger.info("Testing before/after agent callbacks with state updates and streaming")

    # Create agent with both callbacks
    state_updating_agent = LlmAgent(
        name="StateUpdatingAgent",
        model="gemini-2.0-flash-exp",
        instruction="You are a counting agent. When asked to count, respond with numbers from 1 to 20, each number on a separate line. Be precise and consistent.",
        description="Agent demonstrating state updates via callbacks with predictable responses",
        before_agent_callback=before_callback_update_state,
        after_agent_callback=after_callback_update_state
    )
    
    # Create RunConfig with streaming enabled
    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
    
    # Use in-memory runner workflow with streaming config
    await run_in_memory_agent_scenario(
        agent=state_updating_agent,
        user_message="Count from 1 to 20",
        collector=collector,
        app_name="state_update_test_app",
        user_id="test_user_003",
        session_id="test_session_state",
        session_state={"initial_step": "pending"},  # Initial state
        run_config=run_config  # Enable streaming
    )