"""
Sub-Agents Module

This module defines the specialized agents that form the email generation pipeline.
The pipeline follows a sequential processing pattern where each agent performs a
specific task and passes its output to the next agent.

Architecture:
    - Pipeline Pattern: Agents execute in sequence, each building upon previous output
    - Single Responsibility: Each agent has one clear purpose (copy, brand, safety, packaging)
    - State-Based Communication: Agents communicate via shared state keys (output_key)

Pipeline Flow:
    1. CopyAgent: Generates initial email content (subjects + body variants)
    2. BrandAgent: Applies brand guidelines and governance rules
    3. SafetyAgent: Performs compliance and safety checks
    4. PackagingAgent: Combines outputs into final deliverable format
"""

# Standard library imports
import os

# Third-party imports
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

# Local imports
from basic.tools import safety_check_tool
from basic.memory import _load_precreated_brief

# Retry Configuration
# Design: Implements exponential backoff retry strategy for API reliability
# Implementation: Configures HTTP retry behavior for Gemini API calls
# Behavior:
#   - Attempts up to 5 retries on transient failures
#   - Uses exponential backoff with base 7 (delays: 1s, 7s, 49s, 343s, 2401s)
#   - Only retries on specific HTTP status codes indicating transient errors:
#     * 429: Rate limiting (too many requests)
#     * 500: Internal server error
#     * 503: Service unavailable
#     * 504: Gateway timeout
# This ensures resilience against temporary API issues without overwhelming the service
retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier for exponential backoff
    initial_delay=1,  # Initial delay in seconds before first retry
    http_status_codes=[429, 500, 503, 504], # Retry on these HTTP errors
)

# 1) Copy Agent — LLM writes 3 subjects + 2 body variants in strict JSON
# Design: First stage of the pipeline, responsible for creative content generation
# Implementation: Uses LLM to generate multiple variants for A/B testing opportunities
# Behavior:
#   - Reads campaign_brief and creative_guidelines from session state
#   - Generates 3 subject line options (for testing different approaches)
#   - Generates 2 body variants (for personalization or testing)
#   - Outputs structured JSON to ensure downstream agents can parse reliably
#   - Stores output in state under "draft_email" key for next agent
copy_agent = Agent(
    name="CopyAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
You are an email copywriter. You are given a campaign brief and you need to write 3 subject lines and 2 body variants following the creative guidelines.
Campaign brief: {campaign_brief}
Creative guidelines: {creative_guidelines}

Return a STRICT JSON with keys:
{
  "subject_lines": ["...", "...", "..."],
  "body_variants": ["...", "..."]
}
""",
    # State injection mechanism: The {campaign_brief} and {creative_guidelines} placeholders
    # are automatically replaced with values from callback_context.state when the agent runs.
    # The output_key specifies where this agent's result will be stored in state.
    output_key="draft_email",
)

# 2) Brand/Style Agent — post-process via FunctionTool
# Design: Governance layer that ensures brand compliance and style consistency
# Implementation: Uses LLM to review and modify draft content according to guidelines
# Behavior:
#   - Receives draft_email from CopyAgent (via state["draft_email"])
#   - Applies creative_guidelines to ensure brand voice, tone, and style compliance
#   - May modify subject lines or body text to align with brand standards
#   - Outputs the "governed" version that meets all brand requirements
#   - Stores result in state under "governed_email" key
# Note: This agent could potentially use the brand_check FunctionTool for programmatic
# rule enforcement, but currently relies on LLM for more nuanced brand alignment
brand_agent = Agent(
    name="BrandAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
You are a brand/style governance agent. You are given a draft email and you need to apply the creative guidelines to the draft email.
Draft email: {draft_email}
Creative guidelines: {creative_guidelines}
Return the governed email.
""",
    output_key="governed_email",
)

# 3) Safety Agent — run safety_check tool
# Design: Compliance and safety validation layer before deployment
# Implementation: Combines LLM reasoning with programmatic safety_check_tool
# Behavior:
#   - Receives governed_email from BrandAgent (via state["governed_email"])
#   - MUST call safety_check_tool (enforced by instruction) to perform automated checks:
#     * Spam trigger detection (e.g., "free", "guaranteed", "urgent")
#     * PII (Personally Identifiable Information) detection
#     * Other compliance violations
#   - LLM interprets tool results and generates a human-readable safety report
#   - Stores report in state under "safety_report" key for human review
# Critical: This agent MUST call the tool (not optional) to ensure automated safety checks
# are always performed, providing a safety net even if LLM reasoning fails
safety_agent = Agent(
    name="SafetyAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
You are a compliance/safety agent.
You MUST call the safety_check tool with:
- email_content: {governed_email}

Return the safety report.
""",
    tools=[safety_check_tool],
    output_key="safety_report",
)

# 4) Packaging Agent — combines outputs into final format
# Design: Final stage that aggregates all pipeline outputs into a single deliverable
# Implementation: Uses LLM to structure the final output in a consistent JSON format
# Behavior:
#   - Receives both governed_email and safety_report from previous agents
#   - Combines them into a single JSON object for easy consumption
#   - Ensures consistent output format for the root agent and human reviewers
#   - No output_key specified, so output goes to the SequentialAgent's final result
packaging_agent = Agent(
    name="PackagingAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
You are a packaging agent.
You need to package the governed_email and the safety_report into a JSON object.
Return the packaged JSON object.
""",
)

# Sequential Agent Pipeline
# Design: Orchestrates the execution of specialized agents in a defined sequence
# Implementation: Uses SequentialAgent to chain agents together, passing state between them
# Behavior:
#   1. Executes before_agent_callback (_load_precreated_brief) before any agent runs
#      - This loads campaign_brief and creative_guidelines into session state
#   2. Runs copy_agent → brand_agent → safety_agent → packaging_agent in sequence
#   3. Each agent's output (via output_key) becomes available to subsequent agents
#   4. Final output from packaging_agent is returned as the pipeline result
# State Flow:
#   - Initial: campaign_brief, creative_guidelines (from callback)
#   - After copy_agent: draft_email
#   - After brand_agent: governed_email
#   - After safety_agent: safety_report
#   - After packaging_agent: final packaged JSON
initial_email_creator_agent = SequentialAgent(
    name="EmailPipeline",
    sub_agents=[copy_agent, brand_agent, safety_agent, packaging_agent],
    # Callback executed once before the first agent runs
    # Ensures all agents have access to initial campaign data
    before_agent_callback=_load_precreated_brief
    
)



print("✅ Agents defined: Copy, Brand, Safety, Packaging")