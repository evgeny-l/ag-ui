#!/usr/bin/env python
"""Test common LLM scenarios using fixture-based ADK events."""

import pytest
import sys
from pathlib import Path

from ag_ui.core import EventType

sys.path.append(str(Path(__file__).parent / "scenarios"))
from runner_utils import run_fixture_through_translator, compare_ag_ui_events


class TestCommonLLMScenarios:
    """Test common LLM scenarios using generated fixtures."""
    
    @pytest.mark.asyncio
    async def test_single_llm_agent_text_reply(self):
        """Test basic LLM agent text response."""
        
        expected_events = [
            {"type": EventType.TEXT_MESSAGE_START},
            {"type": EventType.TEXT_MESSAGE_CONTENT, "delta": "2 + 2 = 4\n"},
            {"type": EventType.TEXT_MESSAGE_END}
        ]
        
        actual_events = await run_fixture_through_translator("scenario_single_llm_agent_text_reply.json")
        compare_ag_ui_events(actual_events, expected_events)
    
    @pytest.mark.asyncio
    async def test_before_agent_callback(self):
        """Test before_agent_callback functionality."""
        
        expected_events = [
            {"type": EventType.TEXT_MESSAGE_START},
            {"type": EventType.TEXT_MESSAGE_CONTENT, "delta": "Skipped by before_agent_callback due to state condition."},
            {"type": EventType.TEXT_MESSAGE_END}
        ]
        
        actual_events = await run_fixture_through_translator("scenario_before_agent_callback.json")
        compare_ag_ui_events(actual_events, expected_events)
    
    @pytest.mark.asyncio
    async def test_streaming_message_with_states(self):
        """Test streaming LLM responses with state updates."""
        
        expected_events = [
            {"type": EventType.STATE_DELTA, "path": "/processing_step", "value": "started"},
            {"type": EventType.TEXT_MESSAGE_START},
            {"type": EventType.TEXT_MESSAGE_CONTENT, "delta": "1"},
            {"type": EventType.TEXT_MESSAGE_CONTENT, "delta": "\n2\n"},
            {"type": EventType.TEXT_MESSAGE_CONTENT, "delta": "3\n4\n5\n"},
            {"type": EventType.TEXT_MESSAGE_END},
            {"type": EventType.STATE_DELTA, "path": "/processing_step", "value": "completed"}
        ]
        
        actual_events = await run_fixture_through_translator("scenario_streaming_message_with_states.json")
        compare_ag_ui_events(actual_events, expected_events)
    
    @pytest.mark.asyncio
    async def test_streaming_tool_function_call(self):
        """Test streaming LLM responses with function tool usage."""
        
        expected_events = [
            {"type": EventType.TOOL_CALL_START, "tool_call_name": "magic_with_two_numbers"},
            {"type": EventType.TOOL_CALL_ARGS, "delta": '{"first_number": 5, "second_number": 10}'},
            {"type": EventType.TOOL_CALL_END},
            {"type": EventType.TOOL_CALL_RESULT},
            {"type": EventType.TEXT_MESSAGE_START},
            {"type": EventType.TEXT_MESSAGE_CONTENT, "delta": "The magical result is"},
            {"type": EventType.TEXT_MESSAGE_CONTENT, "delta": " 15.\n"},
            {"type": EventType.TEXT_MESSAGE_END}
        ]
        
        actual_events = await run_fixture_through_translator("scenario_streaming_tool_function_call.json")
        compare_ag_ui_events(actual_events, expected_events)