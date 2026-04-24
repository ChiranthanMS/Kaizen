#!/usr/bin/env python3
"""
Add missing columns to app_bills table
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_bills_table():
    # Connect to PostgreSQL
    POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@localhost:5432/travel_expense_db")
    
    try:
        conn = await asyncpg.connect(POSTGRES_URL)
        
        print("🔧 Adding missing columns to app_bills table...")
        
        # Add approved_by column
        try:
            await conn.execute("""
                ALTER TABLE app_bills 
                ADD COLUMN approved_by INTEGER REFERENCES app_users(id)
            """)
            print("✅ Added approved_by column")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️ approved_by column already exists")
            else:
                print(f"❌ Error adding approved_by: {e}")
        
        # Add approved_at column
        try:
            await conn.execute("""
                ALTER TABLE app_bills 
                ADD COLUMN approved_at TIMESTAMP
            """)
            print("✅ Added approved_at column")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️ approved_at column already exists")
            else:
                print(f"❌ Error adding approved_at: {e}")
        
        # Add rejection_reason column
        try:
            await conn.execute("""
                ALTER TABLE app_bills 
                ADD COLUMN rejection_reason TEXT
            """)
            print("✅ Added rejection_reason column")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️ rejection_reason column already exists")
            else:
                print(f"❌ Error adding rejection_reason: {e}")
        
        print("🎉 Table structure updated!")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_bills_table())