"""
MongoDB Service for User Management
Handles all user authentication and profile data storage in MongoDB Atlas
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, DuplicateKeyError
from passlib.context import CryptContext
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MongoDBService:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.password_resets_collection = None
        self.connect()

    def connect(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client["auth_db"]
            self.users_collection = self.db["users"]
            self.password_resets_collection = self.db["password_resets"]
            
            # Create indexes for better performance
            self.create_indexes()
            
            logger.info("✅ MongoDB connected successfully")
            print("MongoDB connected successfully")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            print(f"MongoDB connection failed: {e}")
            raise Exception("MongoDB connection required for user authentication")

    def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Unique indexes for user identification
            self.users_collection.create_index("email", unique=True)
            self.users_collection.create_index("username", unique=True, sparse=True)
            
            # Index for role-based queries
            self.users_collection.create_index("role")
            self.users_collection.create_index("manager_id", sparse=True)
            
            # Index for password reset collection
            self.password_resets_collection.create_index("email")
            self.password_resets_collection.create_index("expires_at", expireAfterSeconds=0)
            
            logger.info("✅ MongoDB indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not create MongoDB indexes: {e}")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in MongoDB
        Returns the created user document
        """
        try:
            # Hash the password
            if 'password' in user_data:
                user_data['password'] = self.hash_password(user_data['password'])
            
            # Add timestamps
            user_data['created_at'] = datetime.utcnow()
            user_data['updated_at'] = datetime.utcnow()
            
            # Set default values
            user_data.setdefault('role', 'employee')
            user_data.setdefault('auth_type', 'regular')
            
            # Insert user
            result = self.users_collection.insert_one(user_data)
            
            # Return the created user (without password)
            created_user = self.users_collection.find_one(
                {"_id": result.inserted_id},
                {"password": 0}  # Exclude password from result
            )
            
            logger.info(f"✅ User created successfully: {user_data.get('email')}")
            return created_user
            
        except DuplicateKeyError as e:
            if 'email' in str(e):
                raise ValueError("Email already registered")
            elif 'username' in str(e):
                raise ValueError("Username already exists")
            else:
                raise ValueError("User already exists")
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            raise Exception(f"Failed to create user: {str(e)}")

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email address"""
        try:
            user = self.users_collection.find_one({"email": email})
            return user
        except Exception as e:
            logger.error(f"❌ Failed to find user by email: {e}")
            return None

    def find_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        try:
            user = self.users_collection.find_one({"username": username})
            return user
        except Exception as e:
            logger.error(f"❌ Failed to find user by username: {e}")
            return None

    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by MongoDB ObjectId"""
        try:
            from bson import ObjectId
            user = self.users_collection.find_one(
                {"_id": ObjectId(user_id)},
                {"password": 0}  # Exclude password
            )
            return user
        except Exception as e:
            logger.error(f"❌ Failed to find user by ID: {e}")
            return None

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password
        Returns user data (without password) if authentication successful
        """
        try:
            # Find user by email
            user = self.find_user_by_email(email)
            if not user:
                return None
            
            # Verify password
            if not self.verify_password(password, user.get('password', '')):
                return None
            
            # Return user data without password
            user_data = {k: v for k, v in user.items() if k != 'password'}
            return user_data
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return None

    def get_employees_for_manager(self, manager_id: str) -> List[Dict[str, Any]]:
        """
        Get all employees under a specific manager
        Returns list of employee data with name, username, email, and registration date
        """
        try:
            from bson import ObjectId
            
            # Find all users with role 'employee' and the specified manager_id
            employees = list(self.users_collection.find(
                {
                    "role": "employee",
                    "manager_id": manager_id
                }
            ).sort("full_name", 1))  # Sort by full name
            
            # Format the response
            formatted_employees = []
            for emp in employees:
                formatted_employees.append({
                    "id": str(emp["_id"]),
                    "name": emp.get("full_name", ""),
                    "username": emp.get("username", ""),
                    "email": emp.get("email", ""),
                    "department": emp.get("department", ""),
                    "registration_date": emp.get("created_at", datetime.utcnow()).isoformat() if emp.get("created_at") else None
                })
            
            logger.info(f"✅ Found {len(formatted_employees)} employees for manager {manager_id}")
            return formatted_employees
            
        except Exception as e:
            logger.error(f"❌ Failed to get employees for manager: {e}")
            return []

    def get_all_employees(self) -> List[Dict[str, Any]]:
        """
        Get all users with role 'employee'
        Returns list of employee data with name, username, email, and registration date
        """
        try:
            employees = list(self.users_collection.find(
                {"role": "employee"}
            ).sort("full_name", 1))  # Sort by full name
            
            # Format the response
            formatted_employees = []
            for emp in employees:
                formatted_employees.append({
                    "id": str(emp["_id"]),
                    "name": emp.get("full_name", ""),
                    "username": emp.get("username", ""),
                    "email": emp.get("email", ""),
                    "department": emp.get("department", ""),
                    "manager_id": emp.get("manager_id", ""),
                    "registration_date": emp.get("created_at", datetime.utcnow()).isoformat() if emp.get("created_at") else None
                })
            
            logger.info(f"✅ Found {len(formatted_employees)} total employees")
            return formatted_employees
            
        except Exception as e:
            logger.error(f"❌ Failed to get all employees: {e}")
            return []

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            from bson import ObjectId
            
            # Add update timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Hash password if provided
            if 'password' in update_data:
                update_data['password'] = self.hash_password(update_data['password'])
            
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to update user: {e}")
            return False

    def store_password_reset_code(self, email: str, code_hash: str, expires_at: datetime):
        """Store password reset code"""
        try:
            self.password_resets_collection.update_one(
                {"email": email},
                {
                    "$set": {
                        "email": email,
                        "code_hash": code_hash,
                        "expires_at": expires_at,
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"✅ Password reset code stored for {email}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store password reset code: {e}")
            raise

    def get_password_reset_record(self, email: str) -> Optional[Dict[str, Any]]:
        """Get password reset record"""
        try:
            record = self.password_resets_collection.find_one({"email": email})
            return record
        except Exception as e:
            logger.error(f"❌ Failed to get password reset record: {e}")
            return None

    def delete_password_reset_record(self, email: str):
        """Delete password reset record"""
        try:
            self.password_resets_collection.delete_one({"email": email})
            logger.info(f"✅ Password reset record deleted for {email}")
        except Exception as e:
            logger.error(f"❌ Failed to delete password reset record: {e}")

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            total_users = self.users_collection.count_documents({})
            total_employees = self.users_collection.count_documents({"role": "employee"})
            total_managers = self.users_collection.count_documents({"role": "manager"})
            
            return {
                "total_users": total_users,
                "total_employees": total_employees,
                "total_managers": total_managers
            }
        except Exception as e:
            logger.error(f"❌ Failed to get user stats: {e}")
            return {}

# Global MongoDB service instance
mongodb_service = MongoDBService()