#!/usr/bin/env python3
"""
API Testing Script for Ajatus Server
Tests all endpoints to ensure they work correctly
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8001"
TEST_WALLET = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"

def test_health_check():
    """Test health check endpoint"""
    print("\n🔍 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "Ajatuskumppani API"
    print("✅ Health check passed")
    print(f"   Fireworks AI: {'✓' if data['fireworks_available'] else '✗'}")
    print(f"   Stripe: {'✓' if data['stripe_configured'] else '✗'}")
    return data

def test_get_balance():
    """Test balance endpoint"""
    print("\n🔍 Testing Get Balance...")
    response = requests.get(
        f"{BASE_URL}/api/balance",
        params={"wallet_address": TEST_WALLET}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["wallet_address"] == TEST_WALLET
    assert "balance" in data
    assert "consumed" in data
    print("✅ Balance check passed")
    print(f"   Balance: {data['balance']} AJT")
    print(f"   Consumed: {data['consumed']} AJT")
    return data

def test_chat_without_api_key():
    """Test chat endpoint without Fireworks API key"""
    print("\n🔍 Testing Chat (without API key)...")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False
        }
    )
    # Should fail gracefully with 503
    assert response.status_code == 503
    data = response.json()
    assert "Fireworks AI not configured" in data["detail"]
    print("✅ Chat error handling works correctly")
    return data

def test_execute_code():
    """Test code execution endpoint"""
    print("\n🔍 Testing Execute Code...")
    response = requests.post(
        f"{BASE_URL}/api/execute-code",
        json={
            "code": "print('Hello, World!')",
            "language": "python"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_implemented"
    print("✅ Execute code endpoint responds correctly")
    return data

def test_create_checkout_without_stripe():
    """Test checkout session creation without Stripe"""
    print("\n🔍 Testing Create Checkout (without Stripe)...")
    response = requests.post(
        f"{BASE_URL}/api/create-checkout-session",
        json={
            "amount": 10000,
            "currency": "usd",
            "success_url": "http://localhost:3000/success",
            "cancel_url": "http://localhost:3000/cancel",
            "wallet_address": TEST_WALLET
        }
    )
    # Should fail gracefully with 503
    assert response.status_code == 503
    data = response.json()
    assert "Stripe not configured" in data["detail"]
    print("✅ Checkout error handling works correctly")
    return data

def test_api_docs():
    """Test API documentation endpoints"""
    print("\n🔍 Testing API Documentation...")
    
    # Test OpenAPI JSON
    response = requests.get(f"{BASE_URL}/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    assert openapi["info"]["title"] == "Ajatuskumppani API"
    
    # Test Swagger UI
    response = requests.get(f"{BASE_URL}/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()
    
    # Test ReDoc
    response = requests.get(f"{BASE_URL}/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()
    
    print("✅ API documentation accessible")
    return openapi

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Ajatus Server API Tests")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Wallet: {TEST_WALLET}")
    
    try:
        # Run tests
        test_health_check()
        test_get_balance()
        test_chat_without_api_key()
        test_execute_code()
        test_create_checkout_without_stripe()
        test_api_docs()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {BASE_URL}")
        print("   Make sure the server is running:")
        print("   python main.py")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

