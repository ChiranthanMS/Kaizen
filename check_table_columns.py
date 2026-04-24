#!/usr/bin/env python3
"""
Check the actual column names in the app_trip_submissions table
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_table_columns():
    """Check what columns actually exist in the database"""
    
    database_url = os.getenv('POSTGRES_URL')
    if not database_url:
        print("❌ POSTGRES_URL not found")
        return
    
    try:
        conn = await asyncpg.connect(database_url)
        
        print("🔍 Checking app_trip_submissions table columns...")
        
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'app_trip_submissions'
            ORDER BY ordinal_position
        """)
        
        if columns:
            print(f"\n📊 Found {len(columns)} columns in app_trip_submissions:")
            for col in columns:
                print(f"   - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        else:
            print("❌ app_trip_submissions table not found")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_table_columns())