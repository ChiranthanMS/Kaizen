#!/usr/bin/env python3
"""
Database setup script to add trip-related columns and tables
Run this script to prepare the database for trip submission flow
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def setup_database():
    """Add trip-related columns and tables to the database"""
    
    # Database connection parameters
    database_url = os.getenv('POSTGRES_URL')
    if not database_url:
        print("❌ POSTGRES_URL not found in environment variables")
        return False
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        # 1. Add trip columns to app_bills table
        print("📝 Adding trip columns to app_bills table...")
        
        try:
            await conn.execute("ALTER TABLE app_bills ADD COLUMN trip_id VARCHAR(100)")
            print("✅ Added trip_id column")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️ trip_id column already exists")
            else:
                print(f"⚠️ Error adding trip_id column: {e}")
        
        try:
            await conn.execute("ALTER TABLE app_bills ADD COLUMN trip_status VARCHAR(20) DEFAULT 'individual'")
            print("✅ Added trip_status column")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️ trip_status column already exists")
            else:
                print(f"⚠️ Error adding trip_status column: {e}")
        
        # 2. Create trip_submissions table
        print("📝 Creating app_trip_submissions table...")
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS app_trip_submissions (
            id SERIAL PRIMARY KEY,
            trip_id VARCHAR(100) NOT NULL,
            employee_id INTEGER NOT NULL,
            employee_name VARCHAR(255),
            trip_purpose TEXT,
            destination_city VARCHAR(100),
            start_date DATE,
            end_date DATE,
            duration_days INTEGER,
            actual_bills_count INTEGER DEFAULT 0,
            actual_total_amount DECIMAL(10,2) DEFAULT 0.00,
            allocated_budget DECIMAL(10,2) DEFAULT 0.00,
            budget_utilization DECIMAL(5,2) DEFAULT 0.00,
            manager_id INTEGER,
            submission_status VARCHAR(20) DEFAULT 'pending',
            submission_notes TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by INTEGER,
            review_comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        await conn.execute(create_table_query)
        print("✅ Created app_trip_submissions table")
        
        # 3. Create indexes
        print("📝 Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_bills_trip_id ON app_bills(trip_id)",
            "CREATE INDEX IF NOT EXISTS idx_bills_trip_status ON app_bills(trip_status)",
            "CREATE INDEX IF NOT EXISTS idx_trip_submissions_employee ON app_trip_submissions(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_trip_submissions_manager ON app_trip_submissions(manager_id)",
            "CREATE INDEX IF NOT EXISTS idx_trip_submissions_status ON app_trip_submissions(submission_status)",
            "CREATE INDEX IF NOT EXISTS idx_trip_submissions_trip_id ON app_trip_submissions(trip_id)"
        ]
        
        for index_query in indexes:
            try:
                await conn.execute(index_query)
                print(f"✅ Created index")
            except Exception as e:
                print(f"⚠️ Index creation warning: {e}")
        
        # 4. Update existing bills
        print("📝 Updating existing bills...")
        await conn.execute("UPDATE app_bills SET trip_status = 'individual' WHERE trip_status IS NULL")
        print("✅ Updated existing bills with trip_status")
        
        # 5. Verify setup
        print("🔍 Verifying setup...")
        
        # Check columns
        columns_result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'app_bills' 
            AND column_name IN ('trip_id', 'trip_status')
        """)
        
        print("📊 app_bills columns:")
        for row in columns_result:
            print(f"   - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        # Check table
        table_result = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'app_trip_submissions'
        """)
        
        if table_result:
            print("✅ app_trip_submissions table exists")
        else:
            print("❌ app_trip_submissions table not found")
        
        # Close connection
        await conn.close()
        
        print("\n🎉 Database setup completed successfully!")
        print("✅ Trip submission flow is now ready to use")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_connection():
    """Test database connection"""
    database_url = os.getenv('POSTGRES_URL')
    if not database_url:
        print("❌ POSTGRES_URL not found in environment variables")
        return False
    
    try:
        print("🧪 Testing database connection...")
        conn = await asyncpg.connect(database_url)
        
        # Test query
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        if result == 1:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection test failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Trip Submission Database Setup")
    print("=" * 50)
    
    # Test connection first
    connection_ok = asyncio.run(test_connection())
    if not connection_ok:
        print("\n❌ Cannot proceed without database connection")
        return 1
    
    # Setup database
    setup_ok = asyncio.run(setup_database())
    
    if setup_ok:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Restart your backend server")
        print("2. Test the trip submission flow")
        print("3. Check the demo instructions in DEMO_INSTRUCTIONS.md")
        return 0
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())