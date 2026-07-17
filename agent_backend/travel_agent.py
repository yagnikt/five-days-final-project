import json
import re
import os
from .mock_flight_api import search_weekend_flights

PREFS_PATH = os.path.join(os.path.dirname(__file__), "preferences.json")

class TravelAgent:
    """
    An ADK-style Agent class that encapsulates the state and skills 
    for monitoring travel deals.
    """
    def __init__(self):
        self.preferences = self._load_prefs()
        self.alerts = []

    def _load_prefs(self):
        if os.path.exists(PREFS_PATH):
            with open(PREFS_PATH, "r") as f:
                return json.load(f)
        return {
            "home_airport": "",
            "destinations": [],
            "max_price": 500,
            "departure_time_preference": "after 5pm Friday",
            "return_time_preference": "Sunday afternoon"
        }

    def _save_prefs(self):
        with open(PREFS_PATH, "w") as f:
            json.dump(self.preferences, f, indent=4)

    def process_chat(self, user_input):
        """Skill: Parse natural language and update preferences."""
        user_input = user_input.lower()
        updated = False
        
        # Origin
        match = re.search(r'(fly out of|from)\s+([a-z]{3})', user_input)
        if match:
            self.preferences["home_airport"] = match.group(2).upper()
            updated = True
            
        # Destinations
        possible_cities = ["miami", "mia", "new york", "jfk", "los angeles", "lax", "london", "lhr"]
        for city in possible_cities:
            if city in user_input and city.upper() not in self.preferences["destinations"]:
                self.preferences["destinations"].append(city.upper())
                updated = True
                
        # Price
        price_match = re.search(r'under \$?(\d+)', user_input)
        if price_match:
            self.preferences["max_price"] = int(price_match.group(1))
            updated = True

        if updated:
            self._save_prefs()
            return f"Got it! I've updated your preferences."
        else:
            return "I'm not sure I caught that. Try saying something like 'I want to fly out of SFO to MIA under $400'."

    def check_flights(self):
        """Skill: Monitor flights based on preferences."""
        origin = self.preferences.get("home_airport")
        destinations = self.preferences.get("destinations", [])
        max_price = self.preferences.get("max_price", 500)
        
        if not origin or not destinations:
            return {"status": "error", "message": "Missing origin or destinations in preferences."}
            
        new_alerts = []
        for dest in destinations:
            flights = search_weekend_flights(origin, dest)
            for flight in flights:
                if flight['price'] <= max_price and flight['is_direct']:
                    # Simplified time check for the prototype
                    new_alerts.append(flight)
                    
        # Deduplicate and save alerts
        self.alerts.extend(new_alerts)
        return {"status": "success", "new_deals_found": len(new_alerts), "deals": new_alerts}

    def get_state(self):
        return {
            "preferences": self.preferences,
            "alerts": self.alerts
        }
