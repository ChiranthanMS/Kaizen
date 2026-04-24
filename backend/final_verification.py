#!/usr/bin/env python3
"""
Final verification script to ensure all TokenData fixes are working
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules import correctly"""
    print("🔍 Testing imports...")
    
    try:
        from main import app
        print("✅ Main app imports successfully")
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        return False
    
    try:
        from models.user_models import TokenData
        print("✅ TokenData model imports successfully")
    except Exception as e:
        print(f"❌ TokenData import failed: {e}")
        return False
    
    try:
        from dependencies.auth_dependencies import get_current_user
        print("✅ Auth dependencies import successfully")
    except Exception as e:
        print(f"❌ Auth dependencies import failed: {e}")
        return False
    
    return True

def test_tokendata_model():
    """Test TokenData model functionality"""
    print("\n🧪 Testing TokenData model...")
    
    try:
        from models.user_models import TokenData
        
        # Test with all fields
        token_data = TokenData(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role="employee",
            full_name="Test User",
            department="IT",
            manager_id="456"
        )
        
        # Test attribute access
        assert token_data.user_id == "123"
        assert token_data.username == "testuser"
        assert token_data.email == "test@example.com"
        assert token_data.role == "employee"
        print("✅ TokenData with all fields works")
        
        # Test with minimal fields
        token_data_minimal = TokenData(
            user_id="123",
            role="employee"
        )
        
        assert token_data_minimal.user_id == "123"
        assert token_data_minimal.role == "employee"
        assert token_data_minimal.username is None
        assert token_data_minimal.email is None
        print("✅ TokenData with minimal fields works")
        
        # Test user identification logic
        user_id = token_data.email or token_data.username or 'unknown'
        assert user_id == "test@example.com"
        
        user_id_minimal = token_data_minimal.email or token_data_minimal.username or 'unknown'
        assert user_id_minimal == "unknown"
        print("✅ User identification logic works")
        
        return True
        
    except Exception as e:
        print(f"❌ TokenData model test failed: {e}")
        return False

def test_route_imports():
    """Test that all route modules import correctly"""
    print("\n📁 Testing route imports...")
    
    routes_to_test = [
        "routes.ocr_routes",
        "routes.ocr_routes_simple", 
        "routes.bill_routes",
        "routes.bill_routes_postgres",
        "routes.analytics_routes",
        "routes.manager_routes"
    ]
    
    success = True
    for route_module in routes_to_test:
        try:
            __import__(route_module)
            print(f"✅ {route_module} imports successfully")
        except Exception as e:
            print(f"❌ {route_module} import failed: {e}")
            success = False
    
    return success

def test_auth_service():
    """Test auth service functionality"""
    print("\n🔐 Testing auth service...")
    
    try:
        from services.auth_service import auth_service
        from models.user_models import TokenData
        
        # Test token creation
        user_data = {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "employee"
        }
        
        token = auth_service.create_access_token(user_data)
        assert isinstance(token, str)
        assert len(token) > 0
        print("✅ Token creation works")
        
        # Test token verification
        token_data = auth_service.verify_token(token)
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == "123"
        assert token_data.email == "test@example.com"
        print("✅ Token verification works")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth service test failed: {e}")
        return False

def test_server_startup():
    """Test that the server can start without errors"""
    print("\n🚀 Testing server startup...")
    
    try:
        from main import app
        
        # Check that the app has routes
        routes = [route.path for route in app.routes]
        
        expected_routes = ["/", "/register", "/login", "/profile"]
        for expected_route in expected_routes:
            if expected_route in routes:
                print(f"✅ Route {expected_route} is registered")
            else:
                print(f"❌ Route {expected_route} is missing")
                return False
        
        print("✅ Server startup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

def main():
    print("🔧 Final Verification: TokenData Fix")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("TokenData Model Tests", test_tokendata_model),
        ("Route Import Tests", test_route_imports),
        ("Auth Service Tests", test_auth_service),
        ("Server Startup Tests", test_server_startup)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            if not test_func():
                all_passed = False
                print(f"❌ {test_name} FAILED")
            else:
                print(f"✅ {test_name} PASSED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ TokenData fix is working correctly")
        print("✅ Server is ready for production")
        print("✅ Bill processing should work without errors")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above and fix them.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)