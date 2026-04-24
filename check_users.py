#!/usr/bin/env python3
"""
Check what users exist in the database
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_users():
    # Connect to PostgreSQL
    POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@localhost:5432/travel_expense_db")
    
    try:
        conn = await asyncpg.connect(POSTGRES_URL)
        
        print("🔍 Checking users in PostgreSQL...")
        
        # Get all users
        users = await conn.fetch("""
            SELECT id, username, email, full_name, role, created_at 
            FROM app_users 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        print(f"📋 Found {len(users)} users:")
        for user in users:
            print(f"  ID: {user['id']}, Email: {user['email']}, Name: {user['full_name']}, Role: {user['role']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_users())