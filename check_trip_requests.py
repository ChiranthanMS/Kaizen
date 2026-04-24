#!/usr/bin/env python3
"""
Check if there are any pending trip requests in the system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.trip_budget_service import trip_budget_service

def check_trip_requests():
    print("🔍 Checking trip requests in the system...")
    
    # Check official trips
    official_trips = trip_budget_service.official_trips
    print(f"📋 Total official trips: {len(official_trips)}")
    
    if official_trips:
        print("\n🎯 Official trips:")
        for trip_id, trip in official_trips.items():
            print(f"  Trip ID: {trip_id}")
            print(f"  Employee: {trip.employee_name}")
            print(f"  Status: {trip.status.value}")
            print(f"  Destination: {trip.destination_city}")
            print(f"  Created: {trip.created_at}")
            print("  ---")
    else:
        print("❌ No official trips found in the system")
        print("💡 This means there are no trip requests to approve")
        print("💡 You need to create a trip request first as an employee")

if __name__ == "__main__":
    check_trip_requests()