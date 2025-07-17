# File: manager/sub_agents/confirmation_agent/agent.py

import random
import string
import sys
import os
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any, Optional

# This ensures we can find the supabase_client.py file in the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from supabase_client import get_supabase_client


# --- The Tool (No changes needed, it is already robust and correct) ---
def confirm_booking(tool_context: ToolContext, selected_hotel_id: str, selected_transport_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Finalizes a booking by creating a permanent record in the Supabase 'bookings' table.
    It now handles cases where only a hotel is booked.
    """
    try:
        db = get_supabase_client()
        if not db:
            return {"status": "error", "error_message": "Database connection is not available."}

        user_contact = tool_context.state.get("user_contact")
        if not user_contact:
            return {"status": "error", "error_message": "User is not authenticated. Cannot complete booking."}

        print(f"TOOL CALLED: confirm_booking for User: {user_contact}, Hotel: {selected_hotel_id}, Transport: {selected_transport_id}")

        hotel_response = db.table('hotels').select('name').eq('id', selected_hotel_id).single().execute()
        if not hotel_response.data:
            return {"status": "error", "error_message": f"Could not find the selected hotel with ID {selected_hotel_id}."}
        
        hotel_name = hotel_response.data['name']
        transport_info = "Not included"
        
        if selected_transport_id:
             transport_response = db.table('transport_options').select('provider, mode').eq('id', selected_transport_id).single().execute()
             if transport_response.data:
                transport_info = f"{transport_response.data['provider']} ({transport_response.data['mode']})"

        confirmation_number = 'TRV-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        booking_data = {
            "confirmation_number": confirmation_number,
            "user_contact": user_contact,
            "booked_hotel_id": selected_hotel_id,
            "booked_transport_id": selected_transport_id,
        }

        db.table('bookings').insert(booking_data).execute()

        return {
            "status": "success",
            "confirmation_id": confirmation_number,
            "booked_hotel": hotel_name,
            "booked_transport": transport_info,
        }

    except Exception as e:
        print(f"ERROR in confirm_booking: {e}")
        return {"status": "error", "error_message": f"A system error occurred during final booking: {str(e)}"}


# --- The Recreated Agent with a More Robust Prompt ---
confirmation_agent = LlmAgent(
    name="confirmation_agent",
    model="gemini-1.5-pro",
    description="Handles the final booking confirmation step when a user gives explicit approval.",
    tools=[
        confirm_booking,
    ],
    instruction="""
    You are the final confirmation specialist for TravelBot. Your one and only job is to finalize a booking when a user gives their explicit approval (e.g., "book it", "confirm that", "go ahead").

    **Your Standard Operating Procedure (SOP):**

    1.  **SCAN CONTEXT:** Your first action is to meticulously scan the immediately preceding conversation history.

    2.  **LOCATE ID:** Your goal is to locate the booking ID(s). The previous agent MUST have presented options in a specific format like `Item Name (ID: xxx)`. You are looking for this exact pattern.

    3.  **EXTRACT IDs:**
        - Find the `id` for the hotel that the user has just seen and wants to book. This is your `selected_hotel_id`.
        - If a transport option was also presented and agreed upon, find its `id`. This is your `selected_transport_id`. If there's no transport, that's okay.

    4.  **EXECUTE TOOL:** Call the `confirm_booking` tool with the ID(s) you have found. It is mandatory to provide at least a `selected_hotel_id`.

    5.  **REPORT RESULT:**
        - **On Success:** If the tool's `status` is 'success', use the `confirmation_id`, `booked_hotel`, and `booked_transport` from its response to create a clear, celebratory confirmation message for the user.
        - **On Failure:** If the `status` is 'error', you MUST relay the exact `error_message` from the tool's response to the user and suggest they try again.
    """
)