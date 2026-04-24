#!/usr/bin/env python3
"""
Fix Supabase table conflicts by creating custom tables
"""

import asyncio
import os
from dotenv import load_dotenv
import asyncpg

# Load environment variables
load_dotenv("../.env")

async def create_custom_tables():
    """Create custom tables for our application"""
    print("🔧 Creating custom tables for Travel Expense App...")
    
    postgres_url = os.getenv("POSTGRES_URL")
    
    try:
        conn = await asyncpg.connect(postgres_url)
        
        # Drop existing conflicting tables if they exist
        print("🗑️ Dropping existing conflicting tables...")
        await conn.execute("DROP TABLE IF EXISTS bills CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS users CASCADE;")
        
        # Create our custom users table
        print("👥 Creating app_users table...")
        await conn.execute("""
            CREATE TABLE app_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                role VARCHAR(20) NOT NULL DEFAULT 'employee',
                department VARCHAR(50),
                manager_id INTEGER REFERENCES app_users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create bills table
        print("🧾 Creating app_bills table...")
        await conn.execute("""
            CREATE TABLE app_bills (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
                filename VARCHAR(255),
                file_type VARCHAR(10),
                date DATE,
                vendor VARCHAR(200),
                category VARCHAR(50),
                amount DECIMAL(10, 2),
                subtotal DECIMAL(10, 2),
                tax DECIMAL(10, 2),
                discount DECIMAL(10, 2),
                currency VARCHAR(3) DEFAULT 'USD',
                remarks TEXT,
                raw_text TEXT,
                confidence_score DECIMAL(3, 2),
                processing_time DECIMAL(5, 2),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        print("📊 Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_app_bills_employee_id ON app_bills(employee_id);
            CREATE INDEX IF NOT EXISTS idx_app_bills_date ON app_bills(date);
            CREATE INDEX IF NOT EXISTS idx_app_bills_category ON app_bills(category);
            CREATE INDEX IF NOT EXISTS idx_app_bills_status ON app_bills(status);
            CREATE INDEX IF NOT EXISTS idx_app_users_role ON app_users(role);
            CREATE INDEX IF NOT EXISTS idx_app_users_manager_id ON app_users(manager_id);
        """)
        
        print("✅ Custom tables created successfully!")
        
        # Insert a test manager user
        print("👤 Creating test manager user...")
        await conn.execute("""
            INSERT INTO app_users (username, email, password_hash, full_name, role, department)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (email) DO NOTHING;
        """, "admin", "admin@company.com", "$2b$12$dummy_hash_for_testing", "System Admin", "manager", "IT")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating custom tables: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 Supabase Table Fix")
    print("=" * 40)
    
    success = await create_custom_tables()
    
    if success:
        print("\n🎉 Tables fixed! Now we need to update the application code to use the new table names.")
    else:
        print("\n❌ Failed to fix tables.")

if __name__ == "__main__":
    asyncio.run(main())