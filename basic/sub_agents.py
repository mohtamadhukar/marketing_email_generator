# Standard library imports
import os

# Third-party imports
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

# Local imports
from basic.tools import safety_check_tool
from basic.memory import _load_precreated_brief
retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504], # Retry on these HTTP errors
)

# 1) Copy Agent — LLM writes 3 subjects + 2 body variants in strict JSON
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
    # The state injection will use keys from the user input (we pass campaign_brief via runner later)
    output_key="draft_email",
)

# 2) Brand/Style Agent — post-process via FunctionTool
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

packaging_agent = Agent(
    name="PackagingAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
You are a packaging agent.
You need to package the governed_email and the safety_report into a JSON object.
Return the packaged JSON object.
""",
)

initial_email_creator_agent = SequentialAgent(
    name="EmailPipeline",
    sub_agents=[copy_agent, brand_agent, safety_agent, packaging_agent],
    before_agent_callback=_load_precreated_brief
    
)



print("✅ Agents defined: Copy, Brand, Safety, Packaging")