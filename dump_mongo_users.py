import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

def dump_users():
    try:
        client = MongoClient(MONGO_URI)
        db = client["auth_db"]
        users_collection = db["users"]
        
        users = list(users_collection.find({}, {"password": 0}))
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"- {user.get('username')} ({user.get('email')}) - Role: {user.get('role')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_users()
