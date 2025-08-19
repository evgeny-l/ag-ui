# ADK Scenarios for Fixture Generation

This directory contains scenarios that use pure Google ADK to generate fixtures for testing without actual LLM execution.

## Setup

1. **Environment Variables**: Create a `.env` file in this directory with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. **Virtual Environment**: Activate the virtual environment from the parent directory:
   ```bash
   cd /path/to/adk-middleware
   source .venv/bin/activate
   ```

## Usage

### List Available Scenarios
```bash
python run.py --list
```

### Run All Scenarios
```bash
python run.py
```

### Run Specific Scenario
```bash
python run.py scenario_name
# Example: python run.py single_llm_agent_text_reply
```

## Scenarios

### 1. single_llm_agent_text_reply
- **Purpose**: Tests basic LLM agent text response
- **Input**: "What is 2+2?"
- **Expected Output**: Mathematical answer from the LLM
- **Fixture**: Contains standard LLM response with usage metadata

### 2. before_agent_callback
- **Purpose**: Tests before_agent_callback functionality
- **Input**: User message with session state `skip_llm_agent: true`
- **Expected Output**: Callback response instead of LLM response
- **Fixture**: Contains callback response with no usage metadata

### 3. streaming_message_with_states
- **Purpose**: Tests streaming LLM responses with before/after agent callbacks updating session state
- **Input**: User message with initial session state
- **Expected Output**: Streaming LLM response with state updates from callbacks
- **Fixture**: Contains 8 events showing streaming chunks with state updates before/after agent execution

### 4. streaming_tool_function_call
- **Purpose**: Tests streaming LLM responses with function tool usage
- **Input**: User message requesting explicit tool usage ("Make magic via tool with 2 numbers: 5 and 10")
- **Expected Output**: Function call, function response, and streaming text response
- **Fixture**: Contains 5 events showing function call → function response → streaming text chunks → final response

## Fixture Generation

- **Deterministic**: Fixtures are generated with consistent IDs and timestamps
- **Location**: `fixtures/scenario_name.json`
- **Format**: JSON with normalized dynamic values:
  - `invocationId`: `invocation_1`, `invocation_2`, etc.
  - `id`: `event_1`, `event_2`, etc.
  - `timestamp`: Fixed value `1234567890.123456`

## Streaming Mode

### Enabling Streaming

To capture streaming events (multiple partial responses), use `RunConfig` with `StreamingMode.SSE`:

```python
from google.adk.runners import RunConfig
from google.adk.agents.run_config import StreamingMode

async def run_scenario(collector) -> None:
    # Create agent
    agent = LlmAgent(
        name="streaming_agent",
        model="gemini-2.0-flash-exp",
        instruction="Your instruction here"
    )
    
    # Create RunConfig with streaming enabled
    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
    
    # Use utility function with streaming config
    await run_in_memory_agent_scenario(
        agent=agent,
        user_message="Your message",
        collector=collector,
        run_config=run_config  # Enable streaming
    )
```

### Streaming vs Non-Streaming Events

- **Non-streaming**: Generates fewer events (typically 1-3)
  - Before callback → Complete response → After callback
- **Streaming**: Generates many events (typically 5-10+)
  - Before callback → Partial chunk 1 → Partial chunk 2 → ... → Final complete response → After callback

### When to Use Streaming

- **Use streaming** when you need to test partial response handling
- **Use non-streaming** for simpler scenarios testing basic functionality
- **Function tools**: Work with both streaming and non-streaming modes
- **Dependencies**: Streaming requires `aiohttp` (install with `uv add aiohttp`)

### Function Tools with Streaming

Function tools can be added to agents and work seamlessly with streaming:

```python
def magic_with_two_numbers(first_number: int, second_number: int) -> int:
    """Simple tool that adds two numbers."""
    return first_number + second_number

async def run_scenario(collector) -> None:
    agent = LlmAgent(
        name="tool_agent",
        model="gemini-2.0-flash-exp",
        instruction="Use the tool when requested",
        tools=[magic_with_two_numbers]  # Add function tools here
    )
    
    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
    await run_in_memory_agent_scenario(
        agent=agent,
        user_message="Make magic via tool with 2 numbers: 5 and 10",
        collector=collector,
        run_config=run_config
    )
```

## Writing Scenarios

### Guidelines

#### **1. Single Purpose**
- Each scenario should test **one specific behavior** or configuration
- Keep scenarios simple and focused
- Don't try to test multiple unrelated features in one scenario

#### **2. Minimal Logging**
- Use `logger` sparingly - only for major scenario-specific steps
- **Don't log**: Setup details, event collection, execution progress
- **Do log**: Key test conditions, important state changes, validation results
- The runner handles all execution details and progress reporting

#### **3. Use Utility Functions**
Available workflow utilities in `runner_utils.py`:
- `run_simple_agent_scenario()` - Basic agent with `Runner`
- `run_in_memory_agent_scenario()` - Agent with `InMemoryRunner`
- Both functions support optional `run_config` parameter for streaming
- Check `runner_utils.py` for the latest available utilities

#### **4. Clean Structure**
```python
import logging
from google.adk.agents.llm_agent import LlmAgent
from runner_utils import run_simple_agent_scenario

logger = logging.getLogger(__name__)

async def run_scenario(collector) -> None:
    """Brief description of what this scenario tests."""
    
    # Create agent with specific configuration for this test
    agent = LlmAgent(
        name="test_agent",
        model="gemini-2.0-flash-exp",
        instruction="Specific instruction for this test"
    )
    
    # Use appropriate utility function
    await run_simple_agent_scenario(
        agent=agent,
        user_message="Test message",
        collector=collector,
        # ... other parameters
    )
```

#### **5. File Naming**
- Use prefix `scenario_` followed by descriptive name
- Example: `scenario_tool_function_call.py`, `scenario_streaming_response.py`

### Examples

#### ✅ Good Scenario (Single Purpose)
```python
async def run_scenario(collector) -> None:
    """Test agent with function calling capability."""
    
    agent = LlmAgent(
        name="function_agent",
        model="gemini-2.0-flash-exp",
        tools=[weather_function]
    )
    
    await run_simple_agent_scenario(
        agent=agent,
        user_message="What's the weather in NYC?",
        collector=collector
    )
```

#### ❌ Bad Scenario (Multiple Purposes)
```python
async def run_scenario(collector) -> None:
    """Test agent with functions, streaming, and callbacks."""  # Too many things!
    
    logger.info("Starting complex test")  # Unnecessary logging
    logger.info("Creating agent...")      # Too verbose
    
    # Tests multiple unrelated features - should be separate scenarios
    # ... complex multi-feature test logic
```

### Adding New Scenarios

1. Create file: `scenario_descriptive_name.py`
2. Implement: `async def run_scenario(collector) -> None`
3. Focus on **one specific test case**
4. Use **existing utility functions** when possible
5. Add **minimal, relevant logging** only
6. The runner automatically discovers and executes new scenarios

**Note**: The runner automatically detects if `run_scenario` is async or sync and handles execution accordingly.

## Writing Tests

### Test Structure Guidelines

Tests should be **clean, minimal, and self-explanatory**. Follow the pattern from `test_scenario_streaming_message_with_states.py`:

#### **1. Clean Test Structure**
```python
#!/usr/bin/env python
"""Test description - one line explaining what's being tested."""

import pytest
import sys
from pathlib import Path

from ag_ui.core import EventType

sys.path.append(str(Path(__file__).parent / "scenarios"))
from runner_utils import run_fixture_through_translator, compare_ag_ui_events


class TestScenarioName:
    """Test class description."""
    
    @pytest.mark.asyncio
    async def test_scenario_name_fixture(self):
        """Test that fixture produces expected AG-UI events."""
        
        expected_events = [
            {"type": EventType.STATE_DELTA, "path": "/key", "value": "value"},
            {"type": EventType.TEXT_MESSAGE_START},
            {"type": EventType.TEXT_MESSAGE_CONTENT, "delta": "text"},
            {"type": EventType.TEXT_MESSAGE_END}
        ]
        
        actual_events = await run_fixture_through_translator("scenario_fixture_file_name.json")
        compare_ag_ui_events(actual_events, expected_events)
```

#### **2. No Excessive Comments**
- **Don't comment obvious one-line actions** like `fixture_data = load_scenario_fixture(...)`
- **Don't explain self-explanatory code** - the test structure is clear
- **Do document** complex event expectations or non-obvious test logic
- **Keep docstrings brief** - one line explaining the test purpose

#### **3. Expected Events Format**
- Use **clear, predictable event sequences**
- Include **only essential properties** for each event type
- **State deltas**: `{"type": EventType.STATE_DELTA, "path": "/key", "value": "value"}`
- **Text content**: `{"type": EventType.TEXT_MESSAGE_CONTENT, "delta": "text"}`
- **Tool calls**: `{"type": EventType.TOOL_CALL_START, "tool_call_name": "function_name"}`

#### **4. Test Naming**
- **File**: `test_scenario_descriptive_name.py`
- **Class**: `TestScenarioDescriptiveName`
- **Method**: `test_scenario_name_fixture`
- **Match scenario file**: `scenario_descriptive_name.py`

#### **5. What NOT to Do**
❌ **Over-commenting**:
```python
# Define what events we expect to see
expected_events = [...]

# Run the fixture through the translator to get actual events
actual_events = await run_fixture_through_translator("scenario_name.json")

# Compare the actual events with expected events
compare_ag_ui_events(actual_events, expected_events)
```

✅ **Clean and minimal**:
```python
expected_events = [...]
actual_events = await run_fixture_through_translator("scenario_name.json")
compare_ag_ui_events(actual_events, expected_events)
```

#### **6. For Future LLM Requests**
When asking an LLM to write tests:
- Reference `test_scenario_streaming_message_with_states.py` as the gold standard
- Emphasize "no excessive comments for self-explanatory actions"
- Request "clean, minimal structure following the example pattern"
- Specify expected event types and their essential properties only

## Event Mocking Implementation

### MockEventFromFixture Class

The `MockEventFromFixture` class in `runner_utils.py` provides proper Event mocking that inherits from the original ADK `Event` class. This ensures all original Event methods work correctly, including:

- **is_final_response()**: Works automatically based on event properties (no manual override needed)
- **get_function_calls()**: Properly extracts function calls from content parts
- **get_function_responses()**: Properly extracts function responses from content parts
- **has_trailing_code_execution_result()**: Checks for trailing code execution results

### Key Benefits

- **Original method behavior**: All Event methods work as designed by ADK
- **Automatic property computation**: No need to manually set computed properties
- **Type safety**: Full compatibility with ADK Event class and its methods
- **Fixture-driven**: Loads all data from fixture files with proper type conversion

### Usage

```python
# Simplified API - pass fixture filename directly
actual_events = await run_fixture_through_translator("scenario_name.json")
compare_ag_ui_events(actual_events, expected_events)

# Or load fixture data explicitly if needed  
fixture_data = load_scenario_fixture("scenario_name.json") 
actual_events = await run_fixture_through_translator(fixture_data)
```

## Architecture

- **runner_utils.py**: Common utilities and workflow functions
- **run.py**: Main runner script that discovers and executes scenarios
- **scenario_*.py**: Individual scenario implementations
- **fixtures/**: Generated deterministic fixture files