#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADK Middleware Scenario Runner.

This script discovers and executes all scenario files in the scenarios directory.
Each scenario generates events that are collected and stored as JSON fixtures
for later testing without actual LLM execution.

Usage:
    python run.py                    # Run all scenarios
    python run.py scenario_name      # Run specific scenario
    python run.py --list             # List available scenarios
"""

import argparse
import sys
from pathlib import Path

from runner_utils import (
    discover_scenarios,
    execute_scenario,
    print_progress,
)


def main():
    """Main entry point for the scenario runner."""
    parser = argparse.ArgumentParser(
        description="Run ADK middleware test scenarios and collect fixtures"
    )
    parser.add_argument(
        "scenario",
        nargs="?",
        help="Specific scenario to run (without scenario_ prefix)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios"
    )
    parser.add_argument(
        "--fixtures-dir",
        default="fixtures",
        help="Directory to save fixture files (default: fixtures)"
    )
    
    args = parser.parse_args()
    
    # Get the scenarios directory
    scenarios_dir = Path(__file__).parent
    fixtures_dir = scenarios_dir / args.fixtures_dir
    
    # Discover available scenarios
    available_scenarios = discover_scenarios(scenarios_dir)
    
    if args.list:
        print("Available scenarios:")
        for scenario in available_scenarios:
            # Remove the 'scenario_' prefix for display
            display_name = scenario.replace("scenario_", "")
            print(f"  - {display_name}")
        return
    
    if not available_scenarios:
        print("No scenario files found in the scenarios directory.")
        print("Scenario files should be named 'scenario_*.py' and contain a 'run_scenario' function.")
        sys.exit(1)
    
    # Determine which scenarios to run
    if args.scenario:
        # Add prefix if not present
        scenario_name = args.scenario
        if not scenario_name.startswith("scenario_"):
            scenario_name = f"scenario_{scenario_name}"
        
        if scenario_name not in available_scenarios:
            print(f"Scenario '{args.scenario}' not found.")
            print(f"Available scenarios: {[s.replace('scenario_', '') for s in available_scenarios]}")
            sys.exit(1)
        
        scenarios_to_run = [scenario_name]
    else:
        scenarios_to_run = available_scenarios
    
    print(f"Found {len(scenarios_to_run)} scenario(s) to execute")
    print(f"Fixtures will be saved to: {fixtures_dir}")
    print("=" * 60)
    
    # Execute scenarios
    successful_runs = 0
    failed_runs = 0
    
    for i, scenario_name in enumerate(scenarios_to_run, 1):
        display_name = scenario_name.replace("scenario_", "")
        print_progress(i, len(scenarios_to_run), display_name, "starting...")
        
        try:
            collector = execute_scenario(scenario_name, scenarios_dir)
            
            if collector is None:
                print_progress(i, len(scenarios_to_run), display_name, "[FAILED] failed to execute")
                failed_runs += 1
                continue
            
            # Save the fixture file
            fixture_path = collector.save_to_fixture(fixtures_dir)
            print_progress(i, len(scenarios_to_run), display_name, "[OK] completed")
            print(f"    Collected {len(collector.events)} events")
            print(f"    Fixture saved: {Path(fixture_path).name}")
            successful_runs += 1
            
        except Exception as e:
            print_progress(i, len(scenarios_to_run), display_name, f"[ERROR] {e}")
            failed_runs += 1
    
    # Summary
    print("=" * 60)
    print(f"Execution complete:")
    print(f"  [OK] Successful: {successful_runs}")
    print(f"  [FAIL] Failed: {failed_runs}")
    print(f"  [DIR] Fixtures directory: {fixtures_dir}")
    
    if failed_runs > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()