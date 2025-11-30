# Standard library imports
import json
import os
from typing import Any, Dict

# Third-party imports
from dotenv import load_dotenv
from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions.state import State

load_dotenv()

SAMPLE_SCENARIO_PATH = f"{os.getenv("DATA_ROOT_FOLDER")}/initial_state.json"

def _set_initial_states(source: Dict[str, Any], target: State | dict[str, Any]):
    """
    Setting the initial session state given a JSON object of states.

    Args:
        source: A JSON object of states.
        target: The session state object to insert into.
    """


    target.update(source)
    print(target)

def _load_precreated_brief(callback_context: CallbackContext):
    """
    Sets up the initial state.
    Set this as a callback as before_agent_call of the root_agent.
    This gets called before the system instruction is contructed.

    Args:
        callback_context: The callback context.
    """    
    data = {}
    with open(SAMPLE_SCENARIO_PATH, "r") as file:
        data = json.load(file)
        print(f"\nLoading Initial State: {data}\n")
    # _set_initial_states(data, callback_context.state)
    callback_context.state['campaign_brief'] = data['campaign_brief']
    callback_context.state['creative_guidelines'] = data['creative_guidelines']