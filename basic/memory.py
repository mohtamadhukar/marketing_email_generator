"""
Memory and State Management Module

This module handles the initialization and management of session state for the email
generation pipeline. It loads initial campaign data from JSON files and injects it
into the agent session state before processing begins.

Design Pattern:
    - State Initialization Pattern: Ensures consistent starting state across agent runs
    - Callback Pattern: Uses before_agent_call callback to inject state before agent execution
    - Configuration via Environment: Uses environment variables for file paths

Behavior:
    - Loads campaign brief and creative guidelines from JSON file
    - Injects data into session state accessible by all agents in the pipeline
    - Executes before agent instructions are constructed, ensuring data is available
"""

# Standard library imports
import json
import os
from typing import Any, Dict

# Third-party imports
from dotenv import load_dotenv
from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions.state import State

# Load environment variables from .env file
# This allows configuration of data paths without hardcoding
load_dotenv()

# Path to the initial state JSON file containing campaign brief and creative guidelines
# Implementation: Constructs path using DATA_ROOT_FOLDER environment variable
# This enables flexible deployment across different environments (dev, staging, prod)
SAMPLE_SCENARIO_PATH = f"{os.getenv("DATA_ROOT_FOLDER")}/initial_state.json"

def _set_initial_states(source: Dict[str, Any], target: State | dict[str, Any]):
    """
    Generic state initialization function.
    
    Design: Provides a flexible way to merge source data into target state object.
    Currently not used but kept for potential future extensibility.
    
    Implementation: Uses dict.update() to merge all keys from source into target.
    This allows bulk state initialization from a JSON configuration.
    
    Args:
        source: A JSON object/dictionary containing state key-value pairs to inject
        target: The session state object (State or dict) to populate with source data
    
    Behavior:
        - Merges all key-value pairs from source into target
        - Overwrites existing keys if they exist in target
        - Prints the updated state for debugging purposes
    """
    target.update(source)
    print(target)

def _load_precreated_brief(callback_context: CallbackContext):
    """
    Callback function to initialize session state with campaign data.
    
    Design: This function is registered as a before_agent_call callback on the
    SequentialAgent. It executes before any agent in the pipeline runs, ensuring
    that campaign_brief and creative_guidelines are available in the session state.
    
    Implementation Details:
        - Reads initial_state.json from the configured data path
        - Extracts campaign_brief and creative_guidelines from the JSON
        - Injects these into callback_context.state for use by all agents
        - Uses selective injection (only specific keys) rather than bulk update
    
    Behavior:
        1. Opens and parses the initial_state.json file
        2. Extracts campaign_brief and creative_guidelines fields
        3. Injects them into the session state dictionary
        4. All subsequent agents can access these via state variables:
           - {campaign_brief} in agent instructions
           - {creative_guidelines} in agent instructions
    
    Args:
        callback_context: The callback context provided by ADK, containing:
            - state: Dictionary-like object for session state storage
            - Other context information about the current agent execution
    
    Note: The commented-out _set_initial_states call suggests this was previously
    used for bulk state injection, but was replaced with selective field injection
    for better control and clarity.
    """    
    data = {}
    with open(SAMPLE_SCENARIO_PATH, "r") as file:
        data = json.load(file)
        print(f"\nLoading Initial State: {data}\n")
    # _set_initial_states(data, callback_context.state)
    # Selective state injection: Only inject the fields needed by the agents
    # This approach provides better control and makes dependencies explicit
    callback_context.state['campaign_brief'] = data['campaign_brief']
    callback_context.state['creative_guidelines'] = data['creative_guidelines']