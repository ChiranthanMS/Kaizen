#!/usr/bin/env python3
"""
Check what trip submission data exists in the database
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def check_submissions_data():
    """Check what trip submission data exists"""
    
    print("🔍 Checking Trip Submissions Data")
    print("=" * 40)
    
    try:
        from database import db_manager
        
        # Connect to database
        await db_manager.connect()
        
        if not db_manager.pool:
            print("❌ Could not connect to database")
            return False
        
        print("✅ Database connected")
        
        print("\n1️⃣ Checking trip submissions table...")
        
        # Get all trip submissions
        submissions = await db_manager.execute_query("""
            SELECT id, trip_id, employee_id, employee_name, trip_purpose, 
                   destination_city, total_bills, total_amount, allocated_budget,
                   submission_status, manager_id, submitted_at
            FROM app_trip_submissions 
            ORDER BY id DESC
        """)
        
        if submissions:
            print(f"✅ Found {len(submissions)} trip submissions:")
            for sub in submissions:
                print(f"   - ID: {sub['id']}")
                print(f"     Trip ID: {sub['trip_id']}")
                print(f"     Employee: {sub['employee_name']} (ID: {sub['employee_id']})")
                print(f"     Purpose: {sub['trip_purpose']}")
                print(f"     Amount: ${sub['total_amount']}")
                print(f"     Status: {sub['submission_status']}")
                print(f"     Manager ID: {sub['manager_id']}")
                print(f"     Submitted: {sub['submitted_at']}")
                print()
        else:
            print("⚠️ No trip submissions found")
        
        print("\n2️⃣ Checking users table...")
        
        # Check users and their roles
        users = await db_manager.execute_query("""
            SELECT id, username, email, full_name, role, manager_id
            FROM app_users 
            ORDER BY id
        """)
        
        if users:
            print(f"✅ Found {len(users)} users:")
            for user in users:
                print(f"   - ID: {user['id']}")
                print(f"     Name: {user['full_name']} ({user['username']})")
                print(f"     Email: {user['email']}")
                print(f"     Role: {user['role']}")
                print(f"     Manager ID: {user['manager_id']}")
                print()
        else:
            print("⚠️ No users found")
        
        print("\n3️⃣ Checking bills associated with trips...")
        
        # Check bills with trip association
        trip_bills = await db_manager.execute_query("""
            SELECT id, employee_id, trip_id, filename, amount, status, trip_status
            FROM app_bills 
            WHERE trip_id IS NOT NULL
            ORDER BY id DESC
            LIMIT 10
        """)
        
        if trip_bills:
            print(f"✅ Found {len(trip_bills)} bills associated with trips:")
            for bill in trip_bills:
                print(f"   - Bill ID: {bill['id']}")
                print(f"     Trip ID: {bill['trip_id']}")
                print(f"     Employee ID: {bill['employee_id']}")
                print(f"     Amount: ${bill['amount']}")
                print(f"     Status: {bill['status']}")
                print(f"     Trip Status: {bill['trip_status']}")
                print()
        else:
            print("⚠️ No bills associated with trips found")
        
        print("\n4️⃣ Testing manager dashboard query...")
        
        # Test the specific query used by manager dashboard
        manager_submissions = await db_manager.get_pending_trip_submissions(manager_id=1)
        
        if manager_submissions:
            print(f"✅ Manager dashboard would show {len(manager_submissions)} submissions:")
            for sub in manager_submissions:
                print(f"   - {sub['trip_purpose']} by {sub['employee_name']}")
                print(f"     Status: {sub['submission_status']}")
                print(f"     Amount: ${sub.get('total_amount', 'N/A')}")
        else:
            print("❌ Manager dashboard query returned no results")
            print("   This explains why the dashboard is empty!")
        
        await db_manager.disconnect()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Trip Submissions Data Check")
    print("=" * 50)
    
    success = asyncio.run(check_submissions_data())
    
    if success:
        print("\n✅ Data check completed")
        print("\nIf no trip submissions were found, that explains why")
        print("the manager dashboard is empty. Try submitting a trip first.")
    else:
        print("\n❌ Data check failed")
    
    return 0

if __name__ == "__main__":
    exit(main())