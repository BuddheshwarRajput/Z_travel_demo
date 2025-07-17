# In orchestrator_agent/agent.py

# --- Import the necessary components ---
from google.adk.agents import LlmAgent
from google.adk.tools import google_search # Use the correct import path

# ... other imports and tool function definitions ...

# --- Create an instance of the Google Search tool ---
# We only need one instance for the whole application.


# ==============================================================================
#  NEW: DEDICATED WEATHER AGENT
# ==============================================================================
weather_details= LlmAgent(
    name="weather_details",
    model="gemini-2.5-pro", # Use the best model for search and summarization
    description="A specialist that provides real-time weather forecasts for any location using Google Search.",
    
    # This agent's ONLY tool is Google Search
    
    
    instruction="""
    You are a dedicated weather forecasting assistant.
    1.  The user will ask for the weather in a specific location.
    2.  Your only job is to use the `GoogleSearch` tool to find the answer.
    3.  Formulate a clear and effective search query, for example: "weather forecast in Manali for the next 3 days".
    4.  Read the search results and summarize them into a direct, easy-to-understand weather report for the user.
    """,
    
    tools=[google_search],
)