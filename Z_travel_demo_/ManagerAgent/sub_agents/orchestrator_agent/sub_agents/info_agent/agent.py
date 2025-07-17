# In the file where your info_agent is defined (e.g., info_agent/agent.py)

# --- All necessary imports ---
from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from tools_common import *
from .weather_details.agent import weather_details



info_agent = LlmAgent(
    name="info_agent",
    model="gemini-1.5-pro", # Corrected to a real, powerful model for synthesis
    description="A fact-finding expert that answers specific questions about destinations or flight statuses.",
    tools=[
        store_trip_parameters,
        agent_tool.AgentTool(agent=weather_details),
        get_destination_info,
        get_emergency_contacts,
        get_current_state,
    ],
    instruction="""
    You are a helpful travel guide. Your job is to answer the user's direct questions by calling a tool and then synthesizing the tool's output into a clear, helpful response.

    **Your Logic:**
    1.  Analyze the user's question to understand what they want to know (e.g., general info, emergency numbers).
    2.  Call the single best tool to get the data (`get_destination_info`, `get_emergency_contacts`, or the weather agent).
    3.  **Synthesize the result:** Once the tool returns a 'success' status, do not just dump the data. Weave it into a helpful paragraph.
        - For `get_destination_info`, combine the `summary` and the list of `popular_attractions` into a nice overview.
        - For `get_emergency_contacts`, present the numbers in a clean, formatted list.
    4.  If the tool returns an 'error', politely inform the user you couldn't find the information.
    """
)