"""Utility functions for running ADK middleware test scenarios."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Awaitable

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from local .env file in scenarios directory
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Ensure API key is available
if not os.getenv("GOOGLE_API_KEY"):
    logger.warning(f"GOOGLE_API_KEY not found in environment variables.")
    logger.warning(f"Expected .env file location: {env_path}")
    logger.warning("Please add GOOGLE_API_KEY to the .env file in the scenarios directory.")

from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.events.event import Event
from google.adk.models.llm_response import LlmResponse


class EventCollector:
    """Collects and stores ADK events during scenario execution."""
    
    def __init__(self, scenario_name: str):
        self.scenario_name = scenario_name
        self.events: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        # For deterministic fixture generation
        self._invocation_id_map: Dict[str, str] = {}
        self._event_id_map: Dict[str, str] = {}
        self._invocation_counter = 0
        self._event_counter = 0
        
    def _normalize_invocation_id(self, invocation_id: str) -> str:
        """Convert dynamic invocation ID to deterministic format."""
        if invocation_id not in self._invocation_id_map:
            self._invocation_counter += 1
            self._invocation_id_map[invocation_id] = f"invocation_{self._invocation_counter}"
        return self._invocation_id_map[invocation_id]
    
    def _normalize_event_id(self, event_id: str) -> str:
        """Convert dynamic event ID to deterministic format."""
        if event_id not in self._event_id_map:
            self._event_counter += 1
            self._event_id_map[event_id] = f"event_{self._event_counter}"
        return self._event_id_map[event_id]
    
    def _normalize_event_dict(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize dynamic values in event dictionary for deterministic fixtures."""
        normalized = event_dict.copy()
        
        # Normalize invocation ID
        if 'invocationId' in normalized and normalized['invocationId']:
            normalized['invocationId'] = self._normalize_invocation_id(normalized['invocationId'])
        
        # Normalize event ID
        if 'id' in normalized and normalized['id']:
            normalized['id'] = self._normalize_event_id(normalized['id'])
        
        # Normalize timestamp to a fixed value
        if 'timestamp' in normalized:
            normalized['timestamp'] = 1234567890.123456
        
        # Normalize function call IDs for deterministic fixtures
        self._normalize_function_call_ids(normalized)
        
        # Remove collected_at as it's always dynamic
        if 'collected_at' in normalized:
            del normalized['collected_at']
        
        return normalized
    
    def _normalize_function_call_ids(self, obj: Any) -> None:
        """Recursively normalize function call IDs to deterministic values."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'functionCall' and isinstance(value, dict) and 'id' in value:
                    # Replace dynamic function call ID with deterministic one
                    value['id'] = 'function_call_1'
                elif key == 'functionResponse' and isinstance(value, dict) and 'id' in value:
                    # Replace dynamic function response ID with deterministic one
                    value['id'] = 'function_call_1'
                else:
                    self._normalize_function_call_ids(value)
        elif isinstance(obj, list):
            for item in obj:
                self._normalize_function_call_ids(item)
    
    def _convert_sets_to_lists(self, obj: Any) -> Any:
        """Recursively convert sets to lists for JSON serialization."""
        if isinstance(obj, set):
            return sorted(list(obj))  # Convert set to sorted list for determinism
        elif isinstance(obj, dict):
            return {key: self._convert_sets_to_lists(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_sets_to_lists(item) for item in obj]
        else:
            return obj

    def collect_event(self, event: Event) -> None:
        """Collect an ADK event for later storage."""
        try:
            event_dict = event.model_dump(by_alias=True)
            # Convert sets to lists for JSON serialization
            event_dict = self._convert_sets_to_lists(event_dict)
            normalized_dict = self._normalize_event_dict(event_dict)
            self.events.append(normalized_dict)
        except Exception as e:
            logger.error(f"Error collecting event: {e}")
            # Create a minimal event representation
            error_event = {
                'id': f'error_event_{len(self.events) + 1}',
                'error_message': f'Failed to serialize event: {str(e)}',
                'timestamp': 1234567890.123456
            }
            self.events.append(error_event)
        
    def collect_llm_response(self, response: LlmResponse) -> None:
        """Collect an LLM response for later storage."""
        response_dict = response.model_dump(by_alias=True)
        response_dict['type'] = 'llm_response'
        normalized_dict = self._normalize_event_dict(response_dict)
        self.events.append(normalized_dict)
        
    def save_to_fixture(self, fixtures_dir: Path) -> str:
        """Save collected events to a JSON fixture file with deterministic content."""
        fixtures_dir.mkdir(exist_ok=True)
        # Use deterministic filename without timestamp
        filename = f"{self.scenario_name}.json"
        filepath = fixtures_dir / filename
        
        # Create deterministic fixture data
        fixture_data = {
            'scenario_name': self.scenario_name,
            'execution_start': '2024-01-01T00:00:00.000000',
            'execution_end': '2024-01-01T00:00:01.000000',
            'events_count': len(self.events),
            'events': self.events
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(fixture_data, f, indent=2, ensure_ascii=False, sort_keys=True)
            
        return str(filepath)


def discover_scenarios(scenarios_dir: Path) -> List[str]:
    """Discover all scenario files in the scenarios directory."""
    scenario_files = []
    for file in scenarios_dir.glob("scenario_*.py"):
        if file.is_file():
            scenario_files.append(file.stem)
    return sorted(scenario_files)


def execute_scenario(scenario_module_name: str, scenarios_dir: Path) -> Optional[EventCollector]:
    """Execute a scenario and return the event collector."""
    try:
        import importlib.util
        import sys
        import inspect
        import asyncio
        
        scenario_path = scenarios_dir / f"{scenario_module_name}.py"
        if not scenario_path.exists():
            logger.error(f"Scenario file not found: {scenario_path}")
            return None
            
        spec = importlib.util.spec_from_file_location(scenario_module_name, scenario_path)
        if spec is None or spec.loader is None:
            logger.error(f"Could not load scenario: {scenario_module_name}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[scenario_module_name] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, 'run_scenario'):
            collector = EventCollector(scenario_module_name)
            
            # Check if run_scenario is async and handle accordingly
            if inspect.iscoroutinefunction(module.run_scenario):
                # Async function - run with asyncio
                asyncio.run(module.run_scenario(collector))
            else:
                # Sync function - run directly
                module.run_scenario(collector)
                
            return collector
        else:
            logger.error(f"Scenario {scenario_module_name} does not have a run_scenario function")
            return None
            
    except Exception as e:
        logger.error(f"Error executing scenario {scenario_module_name}: {e}")
        return None


def print_progress(current: int, total: int, scenario_name: str, status: str = ""):
    """Print execution progress."""
    percentage = (current / total) * 100 if total > 0 else 0
    print(f"[{current}/{total}] ({percentage:.1f}%) {scenario_name} {status}")


def load_fixture(fixture_path: Path) -> Optional[Dict[str, Any]]:
    """Load a fixture file for testing."""
    try:
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading fixture {fixture_path}: {e}")
        return None


def replay_events_from_fixture(fixture_data: Dict[str, Any]) -> List[Event]:
    """Replay events from a fixture file."""
    events = []
    for event_data in fixture_data.get('events', []):
        if event_data.get('type') == 'llm_response':
            continue
        try:
            event = Event(**event_data)
            events.append(event)
        except Exception as e:
            print(f"Error replaying event: {e}")
    return events


# Common ADK workflow functions

async def run_simple_agent_scenario(
    agent: LlmAgent, 
    user_message: str, 
    collector: EventCollector,
    app_name: str = "test_app",
    user_id: str = "test_user",
    session_id: str = "test_session",
    session_state: Optional[Dict[str, Any]] = None,
    run_config: Optional['RunConfig'] = None
) -> None:
    """
    Common workflow for running a simple agent scenario with a single message.
    
    Args:
        agent: The LLM agent to run
        user_message: The message to send to the agent
        collector: Event collector to store events
        app_name: Application name for the session
        user_id: User ID for the session
        session_id: Session ID
        session_state: Optional initial session state
        run_config: Optional RunConfig for advanced configuration (e.g., streaming)
    """
    try:
        # Create session service and session
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=session_state or {}
        )
        
        # Create runner
        runner = Runner(
            agent=agent,
            app_name=app_name,
            session_service=session_service
        )
        
        # Create user message
        content = types.Content(
            role='user',
            parts=[types.Part(text=user_message)]
        )
        
        # Run the agent and collect events
        run_kwargs = {
            'user_id': user_id,
            'session_id': session_id,
            'new_message': content
        }
        if run_config is not None:
            run_kwargs['run_config'] = run_config
            
        async for event in runner.run_async(**run_kwargs):
            # Collect the raw ADK event
            collector.collect_event(event)
            
            # Log only key events
            if hasattr(event, 'error_message') and event.error_message:
                logger.error(f"Event error: {event.error_message}")
            elif event.is_final_response() and event.content:
                if event.content.parts and event.content.parts[0].text:
                    final_answer = event.content.parts[0].text.strip()
                    logger.info(f"Agent response: {final_answer[:50]}{'...' if len(final_answer) > 50 else ''}")
                    
    except Exception as e:
        logger.error(f"Scenario execution failed: {e}")
        # Create error event for collection
        error_event = Event(
            author="system",
            invocation_id=session_id,
            error_message=str(e),
            error_code="SCENARIO_ERROR"
        )
        collector.collect_event(error_event)


async def run_in_memory_agent_scenario(
    agent: LlmAgent, 
    user_message: str, 
    collector: EventCollector,
    app_name: str = "test_app",
    user_id: str = "test_user",
    session_id: str = "test_session",
    session_state: Optional[Dict[str, Any]] = None,
    run_config: Optional['RunConfig'] = None
) -> None:
    """
    Common workflow for running an agent scenario using InMemoryRunner.
    
    Args:
        agent: The LLM agent to run
        user_message: The message to send to the agent
        collector: Event collector to store events
        app_name: Application name for the session
        user_id: User ID for the session
        session_id: Session ID
        session_state: Optional initial session state
        run_config: Optional RunConfig for advanced configuration (e.g., streaming)
    """
    try:
        # Use InMemoryRunner - it includes InMemorySessionService
        runner = InMemoryRunner(agent=agent, app_name=app_name)
        session_service = runner.session_service
        
        # Create session
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=session_state or {}
        )
        
        # Run the agent and collect events
        run_kwargs = {
            'user_id': user_id,
            'session_id': session_id,
            'new_message': types.Content(role="user", parts=[types.Part(text=user_message)])
        }
        if run_config is not None:
            run_kwargs['run_config'] = run_config
            
        async for event in runner.run_async(**run_kwargs):
            # Collect the raw ADK event
            collector.collect_event(event)
            
            # Log only key events
            if hasattr(event, 'error_message') and event.error_message:
                logger.error(f"Event error: {event.error_message}")
            elif event.is_final_response() and event.content:
                if event.content.parts and event.content.parts[0].text:
                    final_answer = event.content.parts[0].text.strip()
                    logger.info(f"Agent response: {final_answer[:50]}{'...' if len(final_answer) > 50 else ''}")
                    
    except Exception as e:
        logger.error(f"Scenario execution failed: {e}")
        # Create error event for collection
        error_event = Event(
            author="system",
            invocation_id=session_id,
            error_message=str(e),
            error_code="SCENARIO_ERROR"
        )
        collector.collect_event(error_event)