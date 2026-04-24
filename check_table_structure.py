#!/usr/bin/env python3
"""
Check the structure of app_bills table
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_table_structure():
    # Connect to PostgreSQL
    POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@localhost:5432/travel_expense_db")
    
    try:
        conn = await asyncpg.connect(POSTGRES_URL)
        
        print("🔍 Checking app_bills table structure...")
        
        # Get table columns
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'app_bills'
            ORDER BY ordinal_position
        """)
        
        print(f"📋 app_bills table columns:")
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())