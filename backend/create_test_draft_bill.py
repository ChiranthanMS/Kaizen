#!/usr/bin/env python3
"""
Create a test draft bill for testing the submission feature
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from database import db_manager
from datetime import datetime, date

async def create_test_draft_bill():
    """Create a test draft bill directly in the database"""
    
    print("🔧 Creating Test Draft Bill")
    print("=" * 30)
    
    try:
        # First, get the employee user ID
        employee_email = "employee_flow_test@example.com"
        
        # Check if user exists in PostgreSQL
        pg_user = await db_manager.get_user_by_email(employee_email)
        
        if not pg_user:
            print(f"✗ Employee {employee_email} not found in PostgreSQL")
            print("  Creating user in PostgreSQL...")
            
            # Create user in PostgreSQL
            user_data = {
                'email': employee_email,
                'username': 'employee_flow_test',
                'full_name': 'Flow Test Employee',
                'role': 'employee',
                'department': 'Engineering',
                'manager_id': None
            }
            
            pg_user_id = await db_manager.create_user(user_data)
            print(f"✓ Created user with ID: {pg_user_id}")
        else:
            pg_user_id = pg_user['id']
            print(f"✓ Found employee with ID: {pg_user_id}")
        
        # Create test draft bill
        bill_data = {
            'employee_id': pg_user_id,
            'filename': 'test_receipt_draft.png',
            'file_type': 'png',
            'date': date(2025, 1, 15),
            'vendor': 'Test Office Store',
            'category': 'Office Supplies',
            'amount': 45.99,
            'subtotal': 42.50,
            'tax': 3.49,
            'discount': 0.00,
            'currency': 'USD',
            'remarks': 'Test draft bill for submission feature',
            'raw_text': 'TEST RECEIPT\nTest Office Store\nDate: 2025-01-15\nOffice Supplies: $42.50\nTax: $3.49\nTotal: $45.99',
            'confidence_score': 0.95,
            'processing_time': 2.5,
            'status': 'draft'  # This is the key - draft status
        }
        
        bill_id = await db_manager.insert_bill(bill_data)
        
        if bill_id:
            print(f"✓ Created test draft bill with ID: {bill_id}")
            print(f"  Employee ID: {pg_user_id}")
            print(f"  Amount: ${bill_data['amount']}")
            print(f"  Vendor: {bill_data['vendor']}")
            print(f"  Status: {bill_data['status']}")
            print(f"  Date: {bill_data['date']}")
            
            # Verify the bill was created
            bills = await db_manager.get_bills_by_employee(pg_user_id, limit=5, offset=0)
            print(f"\n✓ Employee now has {len(bills)} bills")
            
            for bill in bills:
                print(f"  - Bill #{bill['id']}: ${bill['amount']} ({bill['status']})")
            
            print("\n🎯 Test draft bill created successfully!")
            print("   Now you can:")
            print("   1. Login as employee_flow_test@example.com")
            print("   2. Click 'Show My Bills'")
            print("   3. See the draft bill with 'Submit to Manager' button")
            print("   4. Test the submission workflow")
            
        else:
            print("✗ Failed to create test bill")
            
    except Exception as e:
        print(f"❌ Error creating test bill: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_draft_bill())