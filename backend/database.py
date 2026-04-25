import os
import aiosqlite
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import logging
from decimal import Decimal

load_dotenv()

logger = logging.getLogger(__name__)

# SQLite Configuration (replaces PostgreSQL)
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'app_database.db')

class DatabaseManager:
    def __init__(self):
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Initialize database connection"""
        try:
            logger.info(f"Connecting to SQLite database at {SQLITE_DB_PATH}...")
            self.connection = await aiosqlite.connect(SQLITE_DB_PATH)
            self.connection.row_factory = aiosqlite.Row
            logger.info("✅ SQLite connection created successfully")
            
            # Create tables if they don't exist
            await self.create_tables()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to SQLite: {e}")

    async def disconnect(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("SQLite connection closed")

    async def create_tables(self):
        if not self.connection:
            return
            
        create_users_table = """
        CREATE TABLE IF NOT EXISTS app_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        """
        
        create_bills_table = """
        CREATE TABLE IF NOT EXISTS app_bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
            trip_id VARCHAR(50),
            filename VARCHAR(255),
            file_type VARCHAR(10),
            file_hash VARCHAR(64),
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
            trip_status VARCHAR(20) DEFAULT 'individual',
            approved_by INTEGER REFERENCES app_users(id),
            approved_at TIMESTAMP,
            rejection_reason TEXT,
            justification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_trip_submissions_table = """
        CREATE TABLE IF NOT EXISTS app_trip_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id VARCHAR(50) NOT NULL,
            employee_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
            employee_name VARCHAR(100),
            trip_purpose VARCHAR(500),
            destination_city VARCHAR(100),
            start_date DATE,
            end_date DATE,
            duration_days INTEGER,
            total_bills INTEGER DEFAULT 0,
            total_amount DECIMAL(12, 2) DEFAULT 0.00,
            allocated_budget DECIMAL(12, 2) DEFAULT 0.00,
            budget_utilization DECIMAL(5, 2) DEFAULT 0.00,
            submission_status VARCHAR(20) DEFAULT 'submitted',
            manager_id INTEGER REFERENCES app_users(id),
            reviewed_by INTEGER REFERENCES app_users(id),
            reviewed_at TIMESTAMP,
            approval_comments TEXT,
            rejection_reason TEXT,
            justification TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_completed_trips_table = """
        CREATE TABLE IF NOT EXISTS app_completed_trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id VARCHAR(50) NOT NULL UNIQUE,
            employee_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
            employee_name VARCHAR(100),
            trip_purpose VARCHAR(500),
            destination_city VARCHAR(100),
            start_date DATE,
            end_date DATE,
            duration_days INTEGER,
            designation VARCHAR(50),
            city_tier VARCHAR(20),
            allocated_budget DECIMAL(12, 2) DEFAULT 0.00,
            total_bills INTEGER DEFAULT 0,
            total_amount DECIMAL(12, 2) DEFAULT 0.00,
            budget_utilization DECIMAL(5, 2) DEFAULT 0.00,
            trip_status VARCHAR(20) DEFAULT 'completed',
            submission_status VARCHAR(20) DEFAULT 'not_submitted',
            manager_id INTEGER REFERENCES app_users(id),
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            submitted_at TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by INTEGER REFERENCES app_users(id),
            approval_comments TEXT,
            rejection_reason TEXT,
            justification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_app_bills_employee_id ON app_bills(employee_id);",
            "CREATE INDEX IF NOT EXISTS idx_app_bills_trip_id ON app_bills(trip_id);",
            "CREATE INDEX IF NOT EXISTS idx_app_bills_date ON app_bills(date);",
            "CREATE INDEX IF NOT EXISTS idx_app_bills_category ON app_bills(category);",
            "CREATE INDEX IF NOT EXISTS idx_app_bills_status ON app_bills(status);",
            "CREATE INDEX IF NOT EXISTS idx_app_bills_trip_status ON app_bills(trip_status);",
            "CREATE INDEX IF NOT EXISTS idx_app_users_role ON app_users(role);",
            "CREATE INDEX IF NOT EXISTS idx_app_users_manager_id ON app_users(manager_id);",
            "CREATE INDEX IF NOT EXISTS idx_trip_submissions_employee_id ON app_trip_submissions(employee_id);",
            "CREATE INDEX IF NOT EXISTS idx_trip_submissions_trip_id ON app_trip_submissions(trip_id);",
            "CREATE INDEX IF NOT EXISTS idx_trip_submissions_status ON app_trip_submissions(submission_status);",
            "CREATE INDEX IF NOT EXISTS idx_trip_submissions_manager_id ON app_trip_submissions(manager_id);",
            "CREATE INDEX IF NOT EXISTS idx_completed_trips_employee_id ON app_completed_trips(employee_id);",
            "CREATE INDEX IF NOT EXISTS idx_completed_trips_trip_id ON app_completed_trips(trip_id);",
            "CREATE INDEX IF NOT EXISTS idx_completed_trips_status ON app_completed_trips(trip_status);",
            "CREATE INDEX IF NOT EXISTS idx_completed_trips_submission_status ON app_completed_trips(submission_status);",
            "CREATE INDEX IF NOT EXISTS idx_completed_trips_manager_id ON app_completed_trips(manager_id);"
        ]
        
        try:
            await self.connection.execute(create_users_table)
            await self.connection.execute(create_bills_table)
            await self.connection.execute(create_trip_submissions_table)
            await self.connection.execute(create_completed_trips_table)
            
            # Alter existing table for backward compatibility
            try:
                await self.connection.execute("ALTER TABLE app_bills ADD COLUMN file_hash VARCHAR(64);")
            except Exception:
                pass # Column already exists
                
            try:
                await self.connection.execute("ALTER TABLE app_bills ADD COLUMN justification TEXT;")
            except Exception:
                pass # Column already exists

            try:
                await self.connection.execute("ALTER TABLE app_bills ADD COLUMN rejection_reason TEXT;")
            except Exception:
                pass # Column already exists
                
            try:
                await self.connection.execute("ALTER TABLE app_trip_submissions ADD COLUMN justification TEXT;")
            except Exception:
                pass
                
            try:
                await self.connection.execute("ALTER TABLE app_completed_trips ADD COLUMN justification TEXT;")
            except Exception:
                pass

            for idx in create_indexes:
                await self.connection.execute(idx)
            await self.connection.commit()
            logger.info("✅ Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")

    def _convert_decimal(self, obj):
        """Convert Decimal objects to float for SQLite compatibility"""
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (list, tuple)):
            return type(obj)(self._convert_decimal(i) for i in obj)
        if isinstance(obj, dict):
            return {k: self._convert_decimal(v) for k, v in obj.items()}
        return obj

    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        if not self.connection:
            return []
        try:
            # Convert any Decimals in args
            safe_args = self._convert_decimal(args)
            async with self.connection.execute(query.replace('$1', '?').replace('$2', '?').replace('$3', '?').replace('$4', '?').replace('$5', '?').replace('$6', '?').replace('$7', '?').replace('$8', '?').replace('$9', '?').replace('$10', '?').replace('$11', '?').replace('$12', '?').replace('$13', '?').replace('$14', '?').replace('$15', '?').replace('$16', '?').replace('$17', '?').replace('$18', '?').replace('$19', '?'), safe_args) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    async def execute_command(self, command: str, *args) -> str:
        if not self.connection:
            return "ERROR: Database not connected"
        try:
            # Convert any Decimals in args
            safe_args = self._convert_decimal(args)
            cmd = command.replace('$1', '?').replace('$2', '?').replace('$3', '?').replace('$4', '?').replace('$5', '?').replace('$6', '?').replace('$7', '?').replace('$8', '?').replace('$9', '?').replace('$10', '?').replace('$11', '?').replace('$12', '?').replace('$13', '?').replace('$14', '?').replace('$15', '?').replace('$16', '?').replace('$17', '?').replace('$18', '?').replace('$19', '?')
            await self.connection.execute(cmd, safe_args)
            await self.connection.commit()
            return "UPDATE 1"
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return f"ERROR: {str(e)}"

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        if not self.connection:
            return None
        try:
            # Convert any Decimals in args
            safe_args = self._convert_decimal(args)
            cmd = query.replace('$1', '?').replace('$2', '?').replace('$3', '?').replace('$4', '?').replace('$5', '?').replace('$6', '?').replace('$7', '?').replace('$8', '?').replace('$9', '?').replace('$10', '?').replace('$11', '?').replace('$12', '?').replace('$13', '?').replace('$14', '?').replace('$15', '?').replace('$16', '?').replace('$17', '?').replace('$18', '?').replace('$19', '?')
            async with self.connection.execute(cmd, safe_args) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Fetch one failed: {e}")
            return None

    async def insert_bill(self, bill_data: Dict[str, Any]) -> int:
        query = """
        INSERT INTO app_bills (
            employee_id, filename, file_type, file_hash, date, vendor, category,
            amount, subtotal, tax, discount, currency, remarks,
            raw_text, confidence_score, processing_time, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            params = (
                bill_data.get('employee_id'), bill_data.get('filename'), bill_data.get('file_type'),
                bill_data.get('file_hash'), bill_data.get('date'), bill_data.get('vendor'), bill_data.get('category'),
                bill_data.get('amount'), bill_data.get('subtotal'), bill_data.get('tax'),
                bill_data.get('discount'), bill_data.get('currency', 'USD'), bill_data.get('remarks'),
                bill_data.get('raw_text'), bill_data.get('confidence_score'), bill_data.get('processing_time'),
                bill_data.get('status', 'pending')
            )
            # Convert any Decimals
            safe_params = self._convert_decimal(params)
            cursor = await self.connection.execute(query, safe_params)
            await self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to insert bill: {e}")
            raise

    async def insert_bill_with_trip(self, bill_data: Dict[str, Any]) -> int:
        query = """
        INSERT INTO app_bills (
            employee_id, trip_id, filename, file_type, file_hash, date, vendor, category,
            amount, subtotal, tax, discount, currency, remarks,
            raw_text, confidence_score, processing_time, status, trip_status, rejection_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            params = (
                bill_data.get('employee_id'), bill_data.get('trip_id'), bill_data.get('filename'),
                bill_data.get('file_type'), bill_data.get('file_hash'), bill_data.get('date'), bill_data.get('vendor'),
                bill_data.get('category'), bill_data.get('amount'), bill_data.get('subtotal'),
                bill_data.get('tax'), bill_data.get('discount'), bill_data.get('currency', 'USD'),
                bill_data.get('remarks'), bill_data.get('raw_text'), bill_data.get('confidence_score'),
                bill_data.get('processing_time'), bill_data.get('status', 'pending'), bill_data.get('trip_status', 'individual'),
                bill_data.get('rejection_reason')
            )
            # Convert any Decimals
            safe_params = self._convert_decimal(params)
            cursor = await self.connection.execute(query, safe_params)
            await self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to insert bill with trip: {e}")
            return await self.insert_bill(bill_data)

    async def get_bills_by_employee(self, employee_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        query = """
        SELECT b.*, u.username, u.full_name as employee_name, u.email as employee_email
        FROM app_bills b
        JOIN app_users u ON b.employee_id = u.id
        WHERE b.employee_id = ?
        ORDER BY b.created_at DESC
        LIMIT ? OFFSET ?
        """
        return await self.execute_query(query, employee_id, limit, offset)

    async def get_all_bills_for_manager(self, manager_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        query = """
        SELECT b.*, u.username, u.full_name as employee_name, u.email as employee_email,
               u.department
        FROM app_bills b
        JOIN app_users u ON b.employee_id = u.id
        WHERE u.manager_id = ? OR u.id = ?
        ORDER BY b.created_at DESC
        LIMIT ? OFFSET ?
        """
        return await self.execute_query(query, manager_id, manager_id, limit, offset)

    async def get_bills_by_trip(self, trip_id: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM app_bills WHERE trip_id = ? ORDER BY created_at DESC"
        return await self.execute_query(query, trip_id)

    async def get_bill_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        if not file_hash:
            return None
        query = "SELECT * FROM app_bills WHERE file_hash = ?"
        return await self.fetch_one(query, file_hash)

    async def update_bill_justification(self, bill_id: int, justification: str) -> bool:
        query = "UPDATE app_bills SET justification = ?, status = 'under_review', updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        result = await self.execute_command(query, justification, bill_id)
        return "UPDATE" in result

    async def update_trip_justification(self, trip_id: str, justification: str) -> bool:
        """Update justification for a rejected trip submission or completed trip"""
        try:
            # Update trip submission if it exists
            query1 = "UPDATE app_trip_submissions SET justification = ?, submission_status = 'submitted', updated_at = CURRENT_TIMESTAMP WHERE trip_id = ?"
            await self.execute_command(query1, justification, trip_id)
            
            # Update completed trip if it exists
            query2 = "UPDATE app_completed_trips SET justification = ?, submission_status = 'submitted', updated_at = CURRENT_TIMESTAMP WHERE trip_id = ?"
            await self.execute_command(query2, justification, trip_id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update trip justification: {e}")
            return False

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM app_users WHERE id = ?"
        return await self.fetch_one(query, user_id)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM app_users WHERE email = ?"
        return await self.fetch_one(query, email)

    async def create_user(self, user_data: Dict[str, Any]) -> int:
        if not self.connection:
            return None
        query = """
        INSERT INTO app_users (username, email, password_hash, full_name, role, department, manager_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            cursor = await self.connection.execute(
                query,
                (
                    user_data.get('username'), user_data.get('email'), user_data.get('password_hash', ''),
                    user_data.get('full_name'), user_data.get('role', 'employee'), user_data.get('department'),
                    user_data.get('manager_id')
                )
            )
            await self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    async def sync_user_from_mongodb(self, mongo_user: Dict[str, Any]) -> int:
        existing_user = await self.get_user_by_email(mongo_user.get('email'))
        if existing_user:
            return existing_user['id']
        
        user_data = {
            'username': mongo_user.get('username'),
            'email': mongo_user.get('email'),
            'password_hash': '',
            'full_name': mongo_user.get('full_name'),
            'role': mongo_user.get('role', 'employee'),
            'department': mongo_user.get('department'),
            'manager_id': None
        }
        return await self.create_user(user_data)

    async def update_bill_status(self, bill_id: int, status: str) -> bool:
        query = "UPDATE app_bills SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        result = await self.execute_command(query, status, bill_id)
        return "UPDATE" in result

    async def get_bill_statistics(self, employee_id: Optional[int] = None) -> Dict[str, Any]:
        if employee_id:
            query = """
            SELECT 
                COUNT(*) as total_bills,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_bills,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_bills,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_bills
            FROM app_bills 
            WHERE employee_id = ?
            """
            result = await self.fetch_one(query, employee_id)
        else:
            query = """
            SELECT 
                COUNT(*) as total_bills,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_bills,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_bills,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_bills
            FROM app_bills
            """
            result = await self.fetch_one(query)
        return result or {}

    async def create_trip_submission(self, submission_data: Dict[str, Any]) -> int:
        query = """
        INSERT INTO app_trip_submissions (
            trip_id, employee_id, employee_name, trip_purpose, destination_city,
            start_date, end_date, duration_days, total_bills, total_amount,
            allocated_budget, budget_utilization, manager_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            params = (
                submission_data.get('trip_id'), submission_data.get('employee_id'), submission_data.get('employee_name'),
                submission_data.get('trip_purpose'), submission_data.get('destination_city'), submission_data.get('start_date'),
                submission_data.get('end_date'), submission_data.get('duration_days'), submission_data.get('total_bills'),
                submission_data.get('total_amount'), submission_data.get('allocated_budget'), submission_data.get('budget_utilization'),
                submission_data.get('manager_id')
            )
            
            # Convert any Decimals in parameters
            safe_params = self._convert_decimal(params)
            
            cursor = await self.connection.execute(query, safe_params)
            await self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create trip submission: {e}")
            raise

    async def get_trip_bills(self, trip_id: str) -> List[Dict[str, Any]]:
        query = """
        SELECT b.*, u.username, u.full_name as employee_name, u.email as employee_email
        FROM app_bills b
        JOIN app_users u ON b.employee_id = u.id
        WHERE b.trip_id = ?
        ORDER BY b.created_at ASC
        """
        return await self.execute_query(query, trip_id)

    async def get_pending_trip_submissions(self, manager_id: int) -> List[Dict[str, Any]]:
        query = """
        SELECT ts.*, 
               COUNT(b.id) as actual_bills_count,
               COALESCE(SUM(b.amount), 0) as actual_total_amount
        FROM app_trip_submissions ts
        LEFT JOIN app_bills b ON ts.trip_id = b.trip_id
        WHERE ts.submission_status = 'submitted' 
        AND (ts.manager_id = ? OR ts.manager_id IS NULL)
        GROUP BY ts.id
        ORDER BY ts.submitted_at DESC
        """
        return await self.execute_query(query, manager_id)

    async def get_all_pending_trip_submissions(self) -> List[Dict[str, Any]]:
        query = """
        SELECT ts.*, 
               COUNT(b.id) as actual_bills_count,
               COALESCE(SUM(b.amount), 0) as actual_total_amount
        FROM app_trip_submissions ts
        LEFT JOIN app_bills b ON ts.trip_id = b.trip_id
        WHERE ts.submission_status = 'submitted'
        GROUP BY ts.id
        ORDER BY ts.submitted_at DESC
        """
        return await self.execute_query(query)

    async def approve_trip_submission(self, submission_id: int, manager_id: int, comments: str = None) -> bool:
        try:
            check_submission = "SELECT id, trip_id FROM app_trip_submissions WHERE id = ?"
            existing = await self.fetch_one(check_submission, submission_id)
            if not existing:
                return False
            trip_id = existing['trip_id']
            
            update_submission = """
            UPDATE app_trip_submissions 
            SET submission_status = 'approved', 
                reviewed_by = ?, 
                reviewed_at = CURRENT_TIMESTAMP,
                approval_comments = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            await self.connection.execute(update_submission, self._convert_decimal((manager_id, comments, submission_id)))
            
            update_bills = """
            UPDATE app_bills 
            SET status = 'approved',
                trip_status = 'trip_approved',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE trip_id = ?
            """
            await self.connection.execute(update_bills, self._convert_decimal((manager_id, trip_id)))
            
            # Also update the completed trips record if it exists
            update_completed = """
            UPDATE app_completed_trips
            SET submission_status = 'approved',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                approval_comments = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE trip_id = ?
            """
            await self.connection.execute(update_completed, self._convert_decimal((manager_id, comments, trip_id)))
            
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to approve: {e}")
            return False

    async def reject_trip_submission(self, submission_id: int, manager_id: int, reason: str) -> bool:
        try:
            check_submission = "SELECT id, trip_id FROM app_trip_submissions WHERE id = ?"
            existing = await self.fetch_one(check_submission, submission_id)
            if not existing:
                return False
            trip_id = existing['trip_id']

            update_submission = """
            UPDATE app_trip_submissions 
            SET submission_status = 'rejected', 
                reviewed_by = ?, 
                reviewed_at = CURRENT_TIMESTAMP,
                rejection_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            await self.connection.execute(update_submission, self._convert_decimal((manager_id, reason, submission_id)))
            
            update_bills = """
            UPDATE app_bills 
            SET status = 'rejected',
                trip_status = 'trip_rejected',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                rejection_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE trip_id = ?
            """
            await self.connection.execute(update_bills, self._convert_decimal((manager_id, reason, trip_id)))
            
            # Also update the completed trips record if it exists
            update_completed = """
            UPDATE app_completed_trips
            SET submission_status = 'rejected',
                rejection_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE trip_id = ?
            """
            await self.connection.execute(update_completed, self._convert_decimal((reason, trip_id)))
            
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to reject: {e}")
            return False

    async def create_completed_trip(self, trip_data: Dict[str, Any]) -> int:
        query = """
        INSERT INTO app_completed_trips (
            trip_id, employee_id, employee_name, trip_purpose, destination_city,
            start_date, end_date, duration_days, designation, city_tier,
            allocated_budget, total_bills, total_amount, budget_utilization,
            trip_status, submission_status, manager_id, approved_by, approved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(trip_id) DO UPDATE SET
            total_bills = excluded.total_bills,
            total_amount = excluded.total_amount,
            budget_utilization = excluded.budget_utilization,
            trip_status = excluded.trip_status,
            submission_status = excluded.submission_status,
            approved_by = excluded.approved_by,
            approved_at = excluded.approved_at,
            updated_at = CURRENT_TIMESTAMP
        """
        try:
            params = (
                trip_data.get('trip_id'), trip_data.get('employee_id'), trip_data.get('employee_name'),
                trip_data.get('trip_purpose'), trip_data.get('destination_city'), trip_data.get('start_date'),
                trip_data.get('end_date'), trip_data.get('duration_days'), trip_data.get('designation'),
                trip_data.get('city_tier'), trip_data.get('allocated_budget'), trip_data.get('total_bills', 0),
                trip_data.get('total_amount', 0), trip_data.get('budget_utilization', 0),
                trip_data.get('trip_status', 'completed'), trip_data.get('submission_status', 'not_submitted'),
                trip_data.get('manager_id'), trip_data.get('approved_by'), trip_data.get('approved_at')
            )
            # Convert any Decimals
            safe_params = self._convert_decimal(params)
            
            cursor = await self.connection.execute(query, safe_params)
            await self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create completed trip: {e}")
            return None

    async def get_completed_trips_by_employee(self, employee_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = """
        SELECT ct.*, 
               COUNT(b.id) as actual_bills_count,
               COALESCE(SUM(b.amount), 0) as actual_total_amount
        FROM app_completed_trips ct
        LEFT JOIN app_bills b ON ct.trip_id = b.trip_id
        WHERE ct.employee_id = ?
        GROUP BY ct.id
        ORDER BY ct.completed_at DESC
        LIMIT ? OFFSET ?
        """
        return await self.execute_query(query, employee_id, limit, offset)

    async def get_all_completed_trips_for_manager(self, manager_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = """
        SELECT ct.*, 
               COUNT(b.id) as actual_bills_count,
               COALESCE(SUM(b.amount), 0) as actual_total_amount
        FROM app_completed_trips ct
        LEFT JOIN app_bills b ON ct.trip_id = b.trip_id
        WHERE (ct.manager_id = ? OR ct.manager_id IS NULL)
        GROUP BY ct.id
        ORDER BY ct.completed_at DESC
        LIMIT ? OFFSET ?
        """
        return await self.execute_query(query, manager_id, limit, offset)

    async def update_completed_trip_submission_status(self, trip_id: str, status: str, submitted_at=None) -> bool:
        query = """
        UPDATE app_completed_trips 
        SET submission_status = ?,
            submitted_at = COALESCE(?, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
        WHERE trip_id = ?
        """
        result = await self.execute_command(query, status, submitted_at, trip_id)
        return "UPDATE" in result

    async def update_bills_trip_status(self, trip_id: str, trip_status: str) -> bool:
        query = "UPDATE app_bills SET trip_status = ?, updated_at = CURRENT_TIMESTAMP WHERE trip_id = ?"
        result = await self.execute_command(query, trip_status, trip_id)
        return "UPDATE" in result

# Global database manager instance
db_manager = DatabaseManager()

# Startup and shutdown events
async def startup_database():
    await db_manager.connect()

async def shutdown_database():
    await db_manager.disconnect()