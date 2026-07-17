import random
from datetime import datetime, timedelta

def get_upcoming_weekend_dates():
    """Returns the dates for the upcoming Friday and Sunday."""
    today = datetime.now()
    days_ahead_friday = (4 - today.weekday()) % 7
    if days_ahead_friday == 0: # Today is Friday
        days_ahead_friday = 7 # Get next Friday to be safe for planning
    next_friday = today + timedelta(days=days_ahead_friday)
    next_sunday = next_friday + timedelta(days=2)
    return next_friday.strftime('%Y-%m-%d'), next_sunday.strftime('%Y-%m-%d')

def search_weekend_flights(origin, destination):
    """
    Simulates a flight search API. Returns a mix of good and bad flights.
    """
    outbound_date, return_date = get_upcoming_weekend_dates()
    
    flights = []
    
    # Generate 5 random flights
    for i in range(5):
        # 50% chance of being direct
        is_direct = random.choice([True, False])
        
        # Departure time: random between 8 AM and 10 PM
        dep_hour = random.randint(8, 22)
        ret_hour = random.randint(8, 22)
        
        # Price: random between $150 and $800
        price = random.randint(150, 800)
        
        flight = {
            "id": f"FL-{random.randint(1000, 9999)}",
            "origin": origin,
            "destination": destination,
            "outbound_date": outbound_date,
            "outbound_time": f"{dep_hour:02d}:00",
            "return_date": return_date,
            "return_time": f"{ret_hour:02d}:00",
            "is_direct": is_direct,
            "price": price,
            "airline": random.choice(["Delta", "United", "American", "JetBlue", "MockAir"])
        }
        flights.append(flight)
        
    return flights

if __name__ == "__main__":
    # Test the mock API
    print("Upcoming weekend flights SFO -> MIA:")
    for f in search_weekend_flights("SFO", "MIA"):
        print(f)
