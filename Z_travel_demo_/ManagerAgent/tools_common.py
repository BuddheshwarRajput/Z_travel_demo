from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any, List, Optional
import re
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any, Optional, Literal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from supabase_client import get_supabase_client
def store_trip_parameters(
    tool_context: ToolContext,
    destination: Optional[str] = None,
    # CHANGE: Use Optional[str] instead of Optional[Any]. The LLM will pass numbers as strings.
    duration_days: Optional[str] = None, 
    budget: Optional[str] = None, 
    interests: Optional[List[str]] = None,
    origin: Optional[str] = None,
    travel_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Parses and stores key trip parameters into the session state.
    This version uses simple types that the ADK framework can understand.
    """
    try:
        print(f"ROBUST TOOL CALLED: store_trip_parameters with O:{origin}, D:{destination}, Dur:{duration_days}, B:{budget}")

        # ... (The internal logic for robust parsing you added before is still perfect) ...
        # --- Destination ---
        if destination:
            tool_context.state['destination'] = destination

        # --- Duration (Robust Integer Parsing from String) ---
        if duration_days:
            numeric_part = re.search(r'\d+', str(duration_days))
            if numeric_part:
                tool_context.state['duration_days'] = int(numeric_part.group(0))

        
        # --- Origin ---
        if origin:
            tool_context.state['origin'] = origin
            
        # --- Travel Date ---
        if travel_date:
            tool_context.state['travel_date'] = travel_date
            
        
        # --- Budget (Robust Classification from String) ---
        if budget:
            budget_str = str(budget).lower()
            if "low" in budget_str or "budget" in budget_str:
                tool_context.state['budget_level'] = "Budget"
            elif "high" in budget_str or "luxury" in budget_str:
                tool_context.state['budget_level'] = "Luxury"
            else:
                numeric_part = re.search(r'\d+', budget_str)
                if numeric_part:
                    budget_val = int(numeric_part.group(0))
                    if budget_val <= 15000: tool_context.state['budget_level'] = "Budget"
                    elif budget_val >= 50000: tool_context.state['budget_level'] = "Luxury"
                    else: tool_context.state['budget_level'] = "Mid-Range"
                else:
                    tool_context.state['budget_level'] = "Mid-Range"
        
        # ... other parameters like interests, origin, etc. ...
        if interests:
            tool_context.state['interests'] = interests

        return {"status": "success", "message": "State updated successfully."}
    
    except Exception as e:
        print(f"FATAL ERROR in store_trip_parameters: {e}")
        return {"status": "error", "error_message": f"A critical error occurred while saving trip details: {e}"}

def clear_trip_state(tool_context: ToolContext) -> Dict[str, Any]:
    """Resets all travel planning information in the conversation state."""
    # This tool is correct. No changes needed.
    try:
        print("TOOL CALLED: clear_trip_state")
        keys_to_clear = ['destination', 'duration_days', 'budget_level', 'interests', 'origin', 'travel_date', 'calculated_budget_total']
        for key in keys_to_clear:
            if key in tool_context.state: del tool_context.state[key]
        return {"status": "success", "message": "Previous trip state cleared."}
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to clear state: {e}"}

# --- Logic & Generative Tools (No DB connection needed) ---

def get_budget_estimate(tool_context: ToolContext) -> dict:
    """Calculates a budget using state variables."""
    # This tool is correct. Removed the unnecessary DB call.
    try:
        duration_days = int(tool_context.state.get("duration_days"))
        budget_level = tool_context.state.get("budget_level")
        if not all([duration_days, budget_level]):
            return {"status": "error", "error_message": "Missing duration or budget_level."}
        base_cost_per_day = 8000
        multipliers = {"Budget": 0.7, "Mid-Range": 1.2, "Luxury": 2.5}
        total = base_cost_per_day * duration_days * multipliers.get(budget_level, 1.2)
        tool_context.state["calculated_budget_total"] = total
        return {"status": "success", "budget_estimate": {"total_cost": f"₹{total:,.0f}", "level": budget_level}}
    except Exception as e:
        return {"status": "error", "error_message": f"Budget calculation failed: {str(e)}"}

def generate_packing_list(tool_context: ToolContext) -> Dict[str, Any]:
    """Generates a suggested packing list based on the state."""
    # This tool is correct. No changes needed.
    try:
        duration = int(tool_context.state.get("duration_days", 3))
        interests = tool_context.state.get("interests", [])
        items = ["Phone & Charger", "ID", "Cards & Cash", "Toiletries", f"{duration} sets of clothes"]
        if "adventure" in interests: items.extend(["Hiking Shoes", "First-Aid Kit"])
        if "beach" in interests: items.extend(["Swimsuit", "Sunglasses"])
        return {"status": "success", "packing_list": items}
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to generate packing list: {e}"}

def get_current_state(tool_context: ToolContext) -> Dict[str, Any]:
    """A debugging tool that retrieves and returns the current session state."""
    try:
        print("TOOL CALLED: get_current_state")
        current_state_dict = dict(tool_context.state)
        print(f"Current State: {current_state_dict}")
        return {
            "status": "success",
            "current_state": current_state_dict
        }
    except Exception as e:
        print(f"ERROR in get_current_state: {e}")
        return {
            "status": "error",
            "error_message": f"An error occurred while retrieving the state: {str(e)}"
        } 

def search_hotels(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Searches for hotels in the Supabase database. This tool is a robust,
    self-contained unit that handles its own connection, validation, and errors.
    """
    try:
        # It creates its own database connection every time.
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            return {"status": "error", "error_message": "Supabase credentials are not configured."}
        supabase: Client = create_client(url, key)

        # It checks the state for the data it needs BEFORE querying.
        destination = tool_context.state.get("destination")
        budget_level = tool_context.state.get("budget_level")

        if not destination or not budget_level:
            return {"status": "error", "error_message": "To search for hotels, I need to know both your destination and your budget level (e.g., Budget, Mid-Range, or Luxury)."}

        print(f"TOOL CALLED: Searching Supabase for hotels in {destination}, category: {budget_level}")

        response = supabase.table('hotels').select('*') \
            .ilike('location', destination) \
            .eq('category', budget_level) \
            .order('rating', desc=True) \
            .limit(3) \
            .execute()

        results = response.data

        # It gracefully handles the "no results" case.
        if not results:
            return {
                "status": "success",
                "hotels": [],
                "message": f"My search was successful, but I couldn't find any {budget_level} hotels for {destination} in my database. You might want to try a different budget category."
            }
        
        for hotel in results:
            price = hotel.get('price_per_night', 0)
            hotel['price_per_night'] = f"₹{price:,}" # Added comma for thousands

        return {"status": "success", "hotels": results}

    except Exception as e:
        print(f"FATAL ERROR in search_hotels: {e}")
        return {"status": "error", "error_message": f"A critical technical error occurred while searching for hotels: {str(e)}"}


# --- Tool 2: find_flights_trains_or_buses ---
def find_flights_trains_or_buses(
    tool_context: ToolContext,
    mode: Optional[Literal["Flight", "Train", "Bus", "Car"]] = None
) -> Dict[str, Any]:
    """
    Searches for transport options in the Supabase database. This robust tool
    handles its own connection, validation, and errors.
    """
    try:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            return {"status": "error", "error_message": "Supabase credentials are not configured."}
        supabase: Client = create_client(url, key)

        origin = tool_context.state.get("origin")
        destination = tool_context.state.get("destination")

        if not origin or not destination:
            return {"status": "error", "error_message": "To find transport options, I need to know both where you're starting from and where you're going."}

        print(f"TOOL CALLED: Searching Supabase transport from {origin} to {destination}, Mode: {mode or 'Any'}")

        query = supabase.table('transport_options').select('*') \
            .ilike('origin', origin) \
            .ilike('destination', destination)

        if mode:
            query = query.eq('mode', mode.capitalize())

        response = query.execute()
        results = response.data

        if not results:
            search_description = f" for mode '{mode}'" if mode else ""
            return {
                "status": "success",
                "transport_options": [],
                "message": f"My search was successful, but I couldn't find any direct transport options{search_description} from {origin} to {destination} in my database. Would you like me to check for other modes of transport?"
            }

        return {"status": "success", "transport_options": results}

    except Exception as e:
        print(f"FATAL ERROR in find_flights_trains_or_buses: {e}")
        return {"status": "error", "error_message": f"A critical technical error occurred while searching for transport: {str(e)}"}


# --- Tool 3: get_location_suggestions ---
def get_location_suggestions(tool_context: ToolContext) -> dict:
    """
    Retrieves attraction suggestions from Supabase. This robust tool handles
    its own connection, validation, and errors.
    """
    try:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key: return {"status": "error", "error_message": "Supabase credentials not set."}
        db: Client = create_client(url, key)

        destination = tool_context.state.get("destination")
        interests = tool_context.state.get("interests", [])
        
        if not destination:
            return {"status": "error", "error_message": "I need a destination before I can suggest attractions."}

        print(f"TOOL CALLED: Searching Supabase for attractions in {destination}, Interests: {interests}")
        
        query = db.table('attractions').select('name, type, summary').ilike('location', destination)
        
        if interests:
            # Note: Supabase Python `in_` filter expects a list of strings
            interest_list = [i.capitalize() for i in interests]
            query = query.in_('type', interest_list)
        
        response = query.limit(5).execute()
        results = response.data

        if not results:
            return {
                "status": "success",
                "suggestions": [],
                "message": f"My search was successful, but I couldn't find any attractions matching your interests in {destination}. I can give you general suggestions if you'd like."
            }

        return {"status": "success", "suggestions": results}
    except Exception as e:
        print(f"FATAL ERROR in get_location_suggestions: {e}")
        return {"status": "error", "error_message": f"A database error occurred while getting suggestions: {e}"}

def get_destination_info(tool_context: ToolContext, destination: Optional[str]) -> dict:
    """
    Retrieves a general description and a list of popular attractions for a
    destination by querying the Supabase database.
    """
    try:
        # Get the database connection
        db = get_supabase_client() 
        if not db:
             return {"status": "error", "error_message": "Database connection is not available."}

        target_destination = destination or tool_context.state.get("destination")

        if not target_destination:
            return {"status": "error", "error_message": "A destination has not been set. Please tell me which city you're interested in."}
            
        print(f"TOOL CALLED: get_destination_info for {target_destination} from Supabase")
        
        # Query 1: Get the general description (using the 'db' variable)
        desc_response = db.table('destination_details').select('description').eq('location', destination.capitalize()).single().execute()
        description = desc_response.data.get('description', f"A popular travel destination in India.") if desc_response.data else f"A popular travel destination."

        # Query 2: Get the top attractions (using the 'db' variable)
        attr_response = db.table('attractions').select('name, type').eq('location', destination.capitalize()).limit(4).execute()
        attractions = attr_response.data if attr_response.data else []

        return {
            "status": "success",
            "destination_info": {
                "summary": description,
                "popular_attractions": attractions
            }
        }
        
    except Exception as e:
        print(f"ERROR in get_destination_info: {e}")
        return {"status": "error", "error_message": f"An error occurred while fetching destination info: {str(e)}"}


# --- Tool 2: get_emergency_contacts (Corrected) ---
def get_emergency_contacts(tool_context: ToolContext) -> dict:
    """
    Retrieves the general emergency contact numbers for India from the Supabase database.
    """
    try:
        # Get the database connection
        db = get_supabase_client() 
        if not db:
             return {"status": "error", "error_message": "Database connection is not available."}

        print(f"TOOL CALLED: get_emergency_contacts from Supabase")
        
        # Make the query using the 'db' variable
        response = db.table('emergency_contacts').select('type, number, description').execute()
        contacts = response.data

        if not contacts:
            return {"status": "success", "contacts": [], "message": "I could not find any emergency contacts in the database."}

        return {
            "status": "success",
            "contacts": contacts
        }

    except Exception as e:
        print(f"ERROR in get_emergency_contacts: {e}")
        return {"status": "error", "error_message": f"An error occurred while fetching emergency contacts: {str(e)}"}

