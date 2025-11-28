"""
Test script for MT5 REST API
Tests basic functionality without requiring MT5 credentials
"""
import requests
import pytest
import time
from typing import Optional


BASE_URL = "http://localhost:8000"
TEST_CREDENTIALS = {
    "account_number": 1512191081,
    "password": "Test1234!",
    "server": "FTMO-Demo"
}


def test_api_health():
    """Test if API server is running"""
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data.get('status') == 'healthy', "API should report healthy status"
    assert 'active_sessions' in data, "Response should include active_sessions count"
    print(f"✓ API server is healthy - {data.get('active_sessions', 0)} active sessions")


def test_api_root():
    """Test API root endpoint"""
    response = requests.get(f"{BASE_URL}/", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data.get('name') == 'MT5 REST API', "API name should match"
    assert 'version' in data, "Response should include version"
    assert 'endpoints' in data, "Response should include endpoints list"
    print(f"✓ API root endpoint accessible - {data.get('name')} v{data.get('version')}")


def test_api_docs():
    """Test if API documentation is accessible"""
    response = requests.get(f"{BASE_URL}/docs", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert b"swagger" in response.content.lower() or b"openapi" in response.content.lower(), \
        "Documentation should contain OpenAPI/Swagger UI"
    print(f"✓ API documentation accessible at {BASE_URL}/docs")


def test_invalid_login():
    """Test login with invalid credentials (should fail gracefully)"""
    response = requests.post(
        f"{BASE_URL}/api/v1/login",
        json={
            "account_number": 99999999,
            "password": "invalid",
            "server": "Invalid-Server"
        },
        timeout=30  # MT5 connection may take time to fail
    )
    assert response.status_code in [401, 500, 503], \
        f"Invalid login should return 401/500/503, got {response.status_code}"
    
    data = response.json()
    assert 'detail' in data, "Error response should include detail message"
    print(f"✓ Invalid login properly rejected (status {response.status_code})")


def test_unauthorized_access():
    """Test accessing protected endpoint without authentication"""
    response = requests.get(f"{BASE_URL}/api/v1/account", timeout=5)
    assert response.status_code == 403, \
        f"Unauthorized access should return 403, got {response.status_code}"
    print(f"✓ Unauthorized access properly blocked")


def test_commission_not_in_position():
    """Regression test: commission field should not be in TradePosition response"""
    # This test requires valid MT5 credentials and open positions
    # Skip if credentials not available
    pytest.skip("Requires valid MT5 credentials and open positions")
    
    # Uncomment below if you have valid credentials
    # response = requests.post(f"{BASE_URL}/api/v1/login", json=TEST_CREDENTIALS, timeout=10)
    # assert response.status_code == 200
    # token = response.json()["session_token"]
    # 
    # headers = {"Authorization": f"Bearer {token}"}
    # response = requests.get(f"{BASE_URL}/api/v1/positions", headers=headers, timeout=10)
    # assert response.status_code == 200
    # 
    # positions = response.json()
    # if positions:
    #     position = positions[0]
    #     assert 'commission' not in position, "commission should not be in TradePosition"
    #     assert 'ticket' in position, "ticket is required"
    #     assert 'symbol' in position, "symbol is required"
    #     assert 'volume' in position, "volume is required"
    #     assert 'price_open' in position, "price_open is required"
    #     assert 'sl' in position, "sl is required"
    #     assert 'tp' in position, "tp is required"
    #     print(f"✓ Position structure validated (no commission field)")


@pytest.mark.skipif(True, reason="Requires valid MT5 credentials")
def test_positive_path_auth_flow():
    """Test complete authentication flow: login → access → logout → verify 401"""
    # Login
    response = requests.post(f"{BASE_URL}/api/v1/login", json=TEST_CREDENTIALS, timeout=10)
    assert response.status_code == 200, "Login should succeed with valid credentials"
    
    data = response.json()
    assert 'session_token' in data, "Response should include session_token"
    token = data['session_token']
    print(f"✓ Login successful, token received")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Access protected endpoint
    response = requests.get(f"{BASE_URL}/api/v1/positions", headers=headers, timeout=10)
    assert response.status_code == 200, "Positions endpoint should be accessible with valid token"
    print(f"✓ Positions endpoint accessible with token")
    
    # Logout
    response = requests.post(f"{BASE_URL}/api/v1/logout", headers=headers, timeout=10)
    assert response.status_code == 200, "Logout should succeed"
    print(f"✓ Logout successful")
    
    # Verify token is invalidated
    response = requests.get(f"{BASE_URL}/api/v1/positions", headers=headers, timeout=10)
    assert response.status_code == 401, "Token should be invalid after logout"
    print(f"✓ Token properly invalidated after logout")


@pytest.mark.skipif(True, reason="Requires valid MT5 credentials")
def test_session_expiry():
    """Test that expired tokens return 401"""
    # This would require manipulating session expiry time or waiting 24 hours
    # For now, test with an invalid token
    headers = {"Authorization": "Bearer invalid_token_12345"}
    response = requests.get(f"{BASE_URL}/api/v1/account", headers=headers, timeout=5)
    assert response.status_code == 401, "Invalid token should return 401"
    
    data = response.json()
    assert 'detail' in data, "Error should include detail message"
    print(f"✓ Invalid token properly rejected with 401")


def test_cors_headers():
    """Test that CORS headers are present"""
    response = requests.options(f"{BASE_URL}/api/v1/login", timeout=5)
    # In production, this should be more restrictive
    assert 'access-control-allow-origin' in response.headers, "CORS headers should be present"
    print(f"✓ CORS headers configured")


if __name__ == "__main__":
    # Run with pytest
    import sys
    print("="*60)
    print("MT5 REST API - Test Suite")
    print("="*60)
    print("\nRun with: pytest tests/test_mt5_api.py -v")
    print("Or:       python tests/test_mt5_api.py")
    print()
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
