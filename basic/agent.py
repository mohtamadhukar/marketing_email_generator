"""
Root Agent Module

This module defines the root orchestrator agent that manages the end-to-end email generation
and deployment workflow. The root agent coordinates sub-agents, handles human approval,
and manages the final deployment to SFMC (Salesforce Marketing Cloud).

Design Pattern:
    - Orchestrator Pattern: The root agent acts as a coordinator that delegates specialized
      tasks to sub-agents while maintaining control over the overall workflow.
    - Human-in-the-Loop: Implements an approval gate before final deployment to ensure
      quality and compliance.

Behavior:
    1. Triggers the email creation pipeline (initial_email_creator_agent)
    2. Presents results to human for review (safety_report + governed_email)
    3. Executes deployment or rejection based on human decision
"""

# Third-party imports
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

# Local imports
from basic.sub_agents import  initial_email_creator_agent, retry_config
from basic.tools import deploy_email_to_sfmc_tool, reject_email_tool 
from google.adk.tools.agent_tool import AgentTool


# Root Orchestrator Agent
# Design: This agent serves as the entry point and workflow coordinator for the entire
# email generation system. It maintains a high-level view of the process and delegates
# specialized tasks to sub-agents.
#
# Implementation: Uses Gemini 2.5 Flash Lite model with retry configuration for reliability.
# The AgentTool wrapper allows the SequentialAgent (initial_email_creator_agent) to be
# invoked as a tool, enabling the root agent to trigger the entire email creation pipeline.
#
# Behavior Flow:
#   1. Receives user request/context
#   2. Invokes initial_email_creator_agent (via AgentTool) which runs the full pipeline:
#      - Copy generation → Brand governance → Safety check → Packaging
#   3. Receives packaged output containing governed_email and safety_report
#   4. Displays results to human and requests approval
#   5. Based on approval:
#      - APPROVE: Calls deploy_email_to_sfmc_tool to send email to SFMC
#      - REJECT: Calls reject_email_tool to mark email as rejected
root_agent = Agent(
    name="RootAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
    You need to run the initial_email_creator_agent.
    Once completed show the safety_report and the governed_email to the human and ask for approval to send to SFMC. 
    If the human approves, you need to deploy the email to SFMC using the deploy_email_to_sfmc_tool. 
    If the human rejects, you need to reject the email using the reject_email_tool.
    """,
    # Tools available to the root agent:
    # - AgentTool(initial_email_creator_agent): Wraps the sequential pipeline as a callable tool
    # - reject_email_tool: Marks email as rejected when human disapproves
    # - deploy_email_to_sfmc_tool: Deploys approved email to Salesforce Marketing Cloud
    tools=[AgentTool(initial_email_creator_agent), reject_email_tool, deploy_email_to_sfmc_tool],
    
)