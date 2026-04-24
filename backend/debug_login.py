#!/usr/bin/env python3
"""
Debug login functionality step by step
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from passlib.context import CryptContext

# Load environment variables
load_dotenv("../.env")

def test_mongodb_connection():
    """Test MongoDB connection and user lookup"""
    print("🔍 Testing MongoDB connection...")
    
    try:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("❌ MONGO_URI not found in environment")
            return False
            
        client = MongoClient(mongo_uri)
        db = client.auth_db
        users_collection = db.users
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check if our test user exists
        user = users_collection.find_one({"email": "newemployee@test.com"})
        if user:
            print(f"✅ User found: {user.get('email')} - {user.get('full_name')}")
            print(f"   Role: {user.get('role')}")
            print(f"   Password hash exists: {'password' in user}")
            return user
        else:
            print("❌ User not found in MongoDB")
            
            # List all users
            all_users = list(users_collection.find({}, {"email": 1, "username": 1, "role": 1}))
            print(f"📋 Found {len(all_users)} users in database:")
            for u in all_users:
                print(f"   - {u.get('email')} ({u.get('username')}) - {u.get('role')}")
            return None
            
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None

def test_password_verification(user, test_password):
    """Test password verification"""
    print("\n🔍 Testing password verification...")
    
    if not user or 'password' not in user:
        print("❌ No password hash found for user")
        return False
        
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        stored_hash = user['password']
        print(f"Stored hash: {stored_hash[:50]}...")
        
        is_valid = pwd_context.verify(test_password, stored_hash)
        if is_valid:
            print("✅ Password verification successful")
            return True
        else:
            print("❌ Password verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Password verification error: {e}")
        return False

def test_jwt_secret():
    """Test JWT secret key"""
    print("\n🔍 Testing JWT configuration...")
    
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        print("❌ JWT_SECRET_KEY not found")
        return False
    elif jwt_secret == "your_jwt_secret_key_here":
        print("❌ JWT_SECRET_KEY is still default value")
        return False
    else:
        print(f"✅ JWT_SECRET_KEY configured (length: {len(jwt_secret)})")
        return True

def main():
    """Main debug function"""
    print("🚀 Login Debug Test")
    print("=" * 50)
    
    # Test MongoDB
    user = test_mongodb_connection()
    
    # Test password verification
    if user:
        test_password_verification(user, "TestPass123!")
    
    # Test JWT configuration
    test_jwt_secret()
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == "__main__":
    main()