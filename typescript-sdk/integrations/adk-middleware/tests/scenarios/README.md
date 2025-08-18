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

## Fixture Generation

- **Deterministic**: Fixtures are generated with consistent IDs and timestamps
- **Location**: `fixtures/scenario_name.json`
- **Format**: JSON with normalized dynamic values:
  - `invocationId`: `invocation_1`, `invocation_2`, etc.
  - `id`: `event_1`, `event_2`, etc.
  - `timestamp`: Fixed value `1234567890.123456`

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

## Architecture

- **runner_utils.py**: Common utilities and workflow functions
- **run.py**: Main runner script that discovers and executes scenarios
- **scenario_*.py**: Individual scenario implementations
- **fixtures/**: Generated deterministic fixture files