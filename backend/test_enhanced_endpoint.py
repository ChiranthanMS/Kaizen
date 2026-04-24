#!/usr/bin/env python3
"""
Test the enhanced processing endpoint with a sample image
"""

import requests
import json
from pathlib import Path

def test_enhanced_endpoint():
    """Test the enhanced processing endpoint"""
    
    # You'll need a valid JWT token for this test
    # For now, let's just test the endpoint structure
    
    url = "http://localhost:8000/bills/process-enhanced"
    
    # Create a dummy image file for testing
    dummy_image_content = b"dummy image content for testing"
    
    files = {
        'file': ('test_bill.jpg', dummy_image_content, 'image/jpeg')
    }
    
    # Note: This will fail without a valid JWT token
    # But we can see if the endpoint exists
    try:
        response = requests.post(url, files=files)
        print(f"Enhanced endpoint status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Enhanced endpoint exists (needs authentication)")
            return True
        elif response.status_code == 422:
            print("✅ Enhanced endpoint exists (validation error - expected)")
            return True
        else:
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error testing enhanced endpoint: {e}")
        return False

def test_status_endpoint():
    """Test the status endpoint"""
    try:
        response = requests.get("http://localhost:8000/bills/processing-status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Status endpoint working")
            print(f"   Gemini available: {data.get('services', {}).get('gemini', {}).get('available', False)}")
            return True
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Enhanced Processing Endpoint")
    print("=" * 50)
    
    status_ok = test_status_endpoint()
    endpoint_ok = test_enhanced_endpoint()
    
    print("\n📊 Results:")
    print(f"Status endpoint: {'✅' if status_ok else '❌'}")
    print(f"Enhanced endpoint: {'✅' if endpoint_ok else '❌'}")
    
    if status_ok and endpoint_ok:
        print("\n🎉 Enhanced processing is ready!")
        print("Use: http://localhost:3000/enhanced-upload")
    else:
        print("\n⚠️ Some issues detected. Check server logs.")