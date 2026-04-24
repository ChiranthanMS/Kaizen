#!/usr/bin/env python3
"""
Test API endpoints for Enhanced Bill Processing
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_processing_status():
    """Test the processing status endpoint"""
    print("🔍 Testing Processing Status Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/bills/processing-status")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Processing status endpoint working!")
            print(f"   Overall Status: {data.get('overall_status', 'unknown')}")
            print(f"   OCR.Space: {'✅' if data.get('services', {}).get('ocr_space', {}).get('available') else '❌'}")
            print(f"   Gemini: {'✅' if data.get('services', {}).get('gemini', {}).get('available') else '❌'}")
            print(f"   Regex: {'✅' if data.get('services', {}).get('regex_fallback', {}).get('available') else '❌'}")
            return True
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False

def test_health_endpoint():
    """Test basic health endpoint"""
    print("\n💓 Testing Health Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            print("✅ Health endpoint working!")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_docs_endpoint():
    """Test API documentation endpoint"""
    print("\n📚 Testing API Documentation...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        
        if response.status_code == 200:
            print("✅ API documentation available!")
            print(f"   Access at: {BASE_URL}/docs")
            return True
        else:
            print(f"❌ Docs endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Docs endpoint error: {e}")
        return False

def main():
    """Run API tests"""
    print("🧪 Enhanced Bill Processing API - Test Suite")
    print("=" * 60)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test endpoints
    status_ok = test_processing_status()
    health_ok = test_health_endpoint()
    docs_ok = test_docs_endpoint()
    
    # Summary
    print("\n📊 API Test Summary")
    print("-" * 50)
    print(f"Processing Status: {'✅ OK' if status_ok else '❌ Failed'}")
    print(f"Health Check: {'✅ OK' if health_ok else '❌ Failed'}")
    print(f"API Documentation: {'✅ OK' if docs_ok else '❌ Failed'}")
    
    if all([status_ok, health_ok, docs_ok]):
        print("\n🎉 All API endpoints are working!")
        print(f"\n🌐 Access the application:")
        print(f"   Frontend: http://localhost:3000")
        print(f"   Backend API: {BASE_URL}")
        print(f"   API Docs: {BASE_URL}/docs")
        print(f"   Enhanced Upload: http://localhost:3000/enhanced-upload")
    else:
        print("\n⚠️ Some API endpoints have issues. Check server logs.")

if __name__ == "__main__":
    main()