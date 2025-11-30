# Third-party imports
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

# Local imports
from basic.sub_agents import  initial_email_creator_agent, retry_config
from basic.tools import deploy_email_to_sfmc_tool, reject_email_tool 
from google.adk.tools.agent_tool import AgentTool



root_agent = Agent(
    name="RootAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
    You need to run the initial_email_creator_agent.
    Once completed show the safety_report and the governed_email to the human and ask for approval to send to SFMC. 
    If the human approves, you need to deploy the email to SFMC using the deploy_email_to_sfmc_tool. 
    If the human rejects, you need to reject the email using the reject_email_tool.
    """,
    tools=[AgentTool(initial_email_creator_agent), reject_email_tool, deploy_email_to_sfmc_tool],
    
)