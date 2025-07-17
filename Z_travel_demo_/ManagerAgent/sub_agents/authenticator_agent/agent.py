# File: manager/sub_agents/authenticator_agent/agent.py
# This is the final, corrected version of the authenticator.

# --- Part 1: Clean and Correct Imports ---
import re
import sys
import os
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any

# This ensures we can find the supabase_client.py file in the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# This is the ONLY import needed for the database connection.
from supabase_client import get_supabase_client


# --- Part 2: The Refactored, Database-Aware Tool ---
def process_and_authenticate_user(name: str, contact: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Checks if a user exists in the Supabase database. If so, authenticates them.
    If not, adds them to the database and then authenticates them.
    This version correctly handles cases where the user does not yet exist.
    """
    try:
        # Step A: Get the client connection from our factory function
        db = get_supabase_client()
        if not db:
            return {"status": "error", "error_message": "Database connection is not available."}

        print(f"TOOL CALLED: process_and_authenticate_user with Name: {name}, Contact: {contact}")

        if not name or not contact:
            return {"status": "error", "message": "Name or contact information was not provided."}

        # Step B: Use the 'db' variable to interact with the database
        response = db.table('users').select('contact').eq('contact', contact).execute()
        
        user_display_name = name.split()[0]

        if response.data:
            # If response.data is NOT empty, it means we found the user.
            print(f"Returning user found with contact: {contact}")
        else:
            # If response.data IS empty, it means it's a new user.
            print(f"New user. Adding to Supabase: {name}")
            db.table('users').insert({"full_name": name, "contact": contact}).execute()

        # Step C: Update the session state (short-term memory)
        tool_context.state["user_name"] = user_display_name
        tool_context.state["user_contact"] = contact
        tool_context.state["user_authenticated"] = 1
        
        return {
            "status": "success",
            "message": f"Welcome {user_display_name}! You're now authenticated.",
        }
    except Exception as e:
        print(f"ERROR in process_and_authenticate_user: {e}")
        return {"status": "error", "error_message": f"A system error occurred during authentication: {str(e)}"}


# --- Part 3: The Agent Definition (No changes needed here) ---
# In your authenticator_agent/agent.py file

authenticator_agent = LlmAgent(
    name="authenticator_agent",
    model="gemini-1.5-pro",
    description="Greets new users and handles their authentication before any other action can be taken.",
    tools=[
        process_and_authenticate_user,
    ],
    
    # --- The NEW, More Robust Instruction ---
    instruction="""
    You are the friendly and professional gatekeeper for TravelBot. Your primary function is to ensure the user is authenticated before they can proceed. You must handle two possible scenarios.

    **Your Logic:**

    1.  **Check if Already Authenticated:** First, check the session state for `user_authenticated`. If it is `1`, your job is done. Say nothing and end immediately.

    2.  **Handle the User's First Message:** If the user is not authenticated, analyze their first message.
        - **Scenario A: The user gives a simple greeting** (e.g., "hi", "hello").
          - **Your Action:** Respond with a warm, general welcome and ask for their name and contact information.
          - *Example Response:* "Hello! Welcome to TravelBot. To get started, could you please provide your full name and contact information?"

        - **Scenario B: The user gives a direct command** (e.g., "find me a flight", "plan a trip").
          - **Your Action:** Acknowledge their request, but explain that you need to authenticate them first.
          - *Example Response:* "I can certainly help you with finding a flight. But first, to personalize your experience, could you please provide your full name and contact information?"

    3.  **Process Their Details:** Once the user provides their name and contact details, your only action is to immediately call the `process_and_authenticate_user` tool.

    4.  **Confirm and Hand-off:** After the tool returns a 'success' status, use the `message` from the tool's response to welcome the user and then ask how you can help them.

    This protocol ensures that you can handle any type of initial user interaction gracefully.
    """
)