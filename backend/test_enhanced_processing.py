#!/usr/bin/env python3
"""
Test script for the Enhanced Bill Processing System
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.enhanced_bill_processor import enhanced_bill_processor
from services.gemini_service import gemini_service
from services.ocr_space_service import ocr_space_service
from services.regex_bill_parser import regex_bill_parser

# Sample OCR text for testing
SAMPLE_OCR_TEXT = """
RESTAURANT ABC
123 Main Street, City
Phone: (555) 123-4567

Date: 15/01/2024
Invoice: INV-2024-001

BILL DETAILS:
Chicken Curry         ₹250.00
Rice                  ₹80.00
Naan (2)             ₹120.00
Lassi                ₹60.00

Subtotal:            ₹510.00
CGST (9%):           ₹45.90
SGST (9%):           ₹45.90
Total:               ₹601.80

Payment: Card
Thank you for dining with us!
"""

async def test_service_availability():
    """Test if all services are available"""
    print("🔍 Testing Service Availability...")
    print("-" * 50)
    
    # Test OCR.Space
    ocr_available = ocr_space_service.is_available()
    print(f"OCR.Space API: {'✅ Available' if ocr_available else '❌ Not configured'}")
    
    # Test Gemini
    gemini_available = gemini_service.is_available()
    print(f"Gemini 2.0 Flash: {'✅ Available' if gemini_available else '❌ Not configured'}")
    
    # Test Regex (always available)
    print(f"Regex Parser: ✅ Available")
    
    print()
    return ocr_available, gemini_available

async def test_gemini_parsing():
    """Test Gemini parsing with sample text"""
    print("🤖 Testing Gemini 2.0 Flash Parsing...")
    print("-" * 50)
    
    if not gemini_service.is_available():
        print("❌ Gemini API not available - skipping test")
        return None
    
    try:
        result, error = await gemini_service.analyze_bill_async(SAMPLE_OCR_TEXT, "test_bill.txt")
        
        if error:
            print(f"❌ Gemini parsing failed: {error}")
            return None
        
        print("✅ Gemini parsing successful!")
        print(f"   Vendor: {result.get('vendor', 'N/A')}")
        print(f"   Amount: {result.get('amount', 'N/A')}")
        print(f"   Date: {result.get('date', 'N/A')}")
        print(f"   Category: {result.get('category', 'N/A')}")
        print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
        print()
        
        return result
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return None

def test_regex_parsing():
    """Test regex parsing with sample text"""
    print("🔍 Testing Regex Parser...")
    print("-" * 50)
    
    try:
        result = regex_bill_parser.parse_bill_data(SAMPLE_OCR_TEXT, "test_bill.txt")
        
        print("✅ Regex parsing successful!")
        print(f"   Vendor: {result.get('vendor', 'N/A')}")
        print(f"   Amount: {result.get('amount', 'N/A')}")
        print(f"   Date: {result.get('date', 'N/A')}")
        print(f"   Category: {result.get('category', 'N/A')}")
        print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
        print()
        
        return result
        
    except Exception as e:
        print(f"❌ Regex test failed: {e}")
        return None

async def test_enhanced_processor():
    """Test the complete enhanced processing pipeline"""
    print("🚀 Testing Enhanced Processing Pipeline...")
    print("-" * 50)
    
    # Create a dummy file content (we'll skip OCR and use sample text)
    dummy_content = b"dummy image content"
    filename = "test_restaurant_bill.jpg"
    
    try:
        # We can't test the full pipeline without actual image content,
        # but we can test the parsing components
        print("Testing individual components...")
        
        # Test Gemini parsing
        gemini_result = None
        if gemini_service.is_available():
            gemini_result, gemini_error = await gemini_service.analyze_bill_async(SAMPLE_OCR_TEXT, filename)
            if gemini_result:
                print("✅ Gemini component working")
            else:
                print(f"⚠️ Gemini component failed: {gemini_error}")
        
        # Test regex parsing
        regex_result = regex_bill_parser.parse_bill_data(SAMPLE_OCR_TEXT, filename)
        if regex_result:
            print("✅ Regex component working")
        
        # Test service status
        status = enhanced_bill_processor.get_service_status()
        print("✅ Service status check working")
        print(f"   Overall status: {status}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Enhanced processor test failed: {e}")
        return False

def test_environment_setup():
    """Test environment configuration"""
    print("⚙️ Testing Environment Setup...")
    print("-" * 50)
    
    # Check required environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    ocr_key = os.getenv("OCR_SPACE_API_KEY")
    
    print(f"GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Not set'}")
    print(f"OCR_SPACE_API_KEY: {'✅ Set' if ocr_key else '❌ Not set'}")
    
    if gemini_key:
        print(f"   Gemini key length: {len(gemini_key)} characters")
    if ocr_key:
        print(f"   OCR key length: {len(ocr_key)} characters")
    
    print()
    return bool(gemini_key or ocr_key)

async def main():
    """Run all tests"""
    print("🧪 Enhanced Bill Processing System - Test Suite")
    print("=" * 60)
    print()
    
    # Test environment
    env_ok = test_environment_setup()
    
    # Test service availability
    ocr_available, gemini_available = await test_service_availability()
    
    # Test individual components
    gemini_result = await test_gemini_parsing()
    regex_result = test_regex_parsing()
    
    # Test enhanced processor
    processor_ok = await test_enhanced_processor()
    
    # Summary
    print("📊 Test Summary")
    print("-" * 50)
    print(f"Environment Setup: {'✅ OK' if env_ok else '❌ Issues'}")
    print(f"OCR.Space Service: {'✅ Available' if ocr_available else '❌ Unavailable'}")
    print(f"Gemini Service: {'✅ Available' if gemini_available else '❌ Unavailable'}")
    print(f"Regex Parser: ✅ Available")
    print(f"Enhanced Processor: {'✅ OK' if processor_ok else '❌ Issues'}")
    
    if gemini_result and regex_result:
        print("\n🎯 Parsing Comparison:")
        print(f"Gemini Amount: {gemini_result.get('amount', 'N/A')}")
        print(f"Regex Amount: {regex_result.get('amount', 'N/A')}")
        print(f"Gemini Confidence: {gemini_result.get('confidence_score', 'N/A')}")
        print(f"Regex Confidence: {regex_result.get('confidence_score', 'N/A')}")
    
    print("\n" + "=" * 60)
    
    if not env_ok:
        print("⚠️ Warning: Set up API keys in .env file for full functionality")
    
    if gemini_available and ocr_available:
        print("🎉 All systems ready! Enhanced processing is fully operational.")
    elif gemini_available or ocr_available:
        print("⚠️ Partial functionality available. Some services may be degraded.")
    else:
        print("❌ Limited functionality. Only regex parsing available.")

if __name__ == "__main__":
    asyncio.run(main())