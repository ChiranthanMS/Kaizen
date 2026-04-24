#!/usr/bin/env python3
"""
Debug Manager-Employee Relationship
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mongodb_service import mongodb_service

def debug_manager_employee():
    """Debug the manager-employee relationship"""
    
    print("🔍 Debugging Manager-Employee Relationship")
    print("=" * 50)
    
    # Find the test manager
    manager = mongodb_service.find_user_by_email("manager_flow_test@example.com")
    if manager:
        manager_id = str(manager["_id"])
        print(f"✓ Manager found: {manager.get('full_name')}")
        print(f"  Manager ID: {manager_id}")
        print(f"  Email: {manager.get('email')}")
        print(f"  Role: {manager.get('role')}")
    else:
        print("✗ Manager not found")
        return
    
    # Find the test employee
    employee = mongodb_service.find_user_by_email("employee_flow_test@example.com")
    if employee:
        print(f"\n✓ Employee found: {employee.get('full_name')}")
        print(f"  Employee ID: {str(employee['_id'])}")
        print(f"  Email: {employee.get('email')}")
        print(f"  Role: {employee.get('role')}")
        print(f"  Manager ID: {employee.get('manager_id')}")
        print(f"  Department: {employee.get('department')}")
    else:
        print("✗ Employee not found")
        return
    
    # Check if manager_id matches
    if employee.get('manager_id') == manager_id:
        print("\n✅ Manager-Employee relationship is correct")
    else:
        print(f"\n⚠️ Manager-Employee relationship mismatch:")
        print(f"  Employee's manager_id: {employee.get('manager_id')}")
        print(f"  Actual manager_id: {manager_id}")
        
        # Update the employee's manager_id
        print("\n🔧 Fixing manager_id...")
        success = mongodb_service.update_user(str(employee["_id"]), {"manager_id": manager_id})
        if success:
            print("✅ Employee's manager_id updated successfully")
        else:
            print("✗ Failed to update employee's manager_id")
    
    # Test the get_employees_for_manager function
    print(f"\n🔍 Testing get_employees_for_manager({manager_id})...")
    employees = mongodb_service.get_employees_for_manager(manager_id)
    print(f"Found {len(employees)} employees:")
    
    for emp in employees:
        print(f"  - {emp['name']} ({emp['email']})")
        print(f"    Department: {emp['department']}")
        print(f"    Registration: {emp['registration_date']}")

if __name__ == "__main__":
    debug_manager_employee()