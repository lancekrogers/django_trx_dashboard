#!/usr/bin/env python
"""
Quick API test script to verify all endpoints are working
Run with: python test_api.py
"""

import requests

BASE_URL = "http://localhost:8000/api"

# Test credentials
TEST_EMAIL = "user0@example.com"
TEST_PASSWORD = "testpass123"


def test_auth():
    """Test authentication endpoints"""
    print("\n=== Testing Authentication ===")

    # Login
    response = requests.post(
        f"{BASE_URL}/auth/login/", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    if response.status_code == 200:
        tokens = response.json()
        print("✓ Login successful")
        print(f"  Access token: {tokens['access'][:50]}...")
        return tokens["access"]
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.json())
        return None


def test_wallets(token):
    """Test wallet endpoints"""
    print("\n=== Testing Wallets ===")
    headers = {"Authorization": f"Bearer {token}"}

    # List wallets
    response = requests.get(f"{BASE_URL}/v1/wallets/", headers=headers)
    if response.status_code == 200:
        wallets = response.json()
        print(f"✓ List wallets: Found {len(wallets)} wallets")
        for wallet in wallets[:3]:  # Show first 3
            print(f"  - {wallet['label']} ({wallet['chain']})")
        return wallets[0]["id"] if wallets else None
    else:
        print(f"✗ List wallets failed: {response.status_code}")
        return None


def test_portfolio(token):
    """Test portfolio endpoints"""
    print("\n=== Testing Portfolio ===")
    headers = {"Authorization": f"Bearer {token}"}

    # Portfolio summary
    response = requests.get(f"{BASE_URL}/v1/portfolio/summary", headers=headers)
    if response.status_code == 200:
        summary = response.json()
        print("✓ Portfolio summary:")
        print(f"  Total value: ${summary['total_value_usd']:,.2f}")
        print(f"  24h change: {summary['change_24h']:.2f}%")
        print(f"  Wallets: {summary['wallet_count']}")
    else:
        print(f"✗ Portfolio summary failed: {response.status_code}")

    # Historical data
    response = requests.get(
        f"{BASE_URL}/v1/portfolio/history?period=24h", headers=headers
    )
    if response.status_code == 200:
        history = response.json()
        print(f"✓ Portfolio history: {len(history)} data points")
    else:
        print(f"✗ Portfolio history failed: {response.status_code}")


def test_transactions(token):
    """Test transaction endpoints"""
    print("\n=== Testing Transactions ===")
    headers = {"Authorization": f"Bearer {token}"}

    # List transactions
    response = requests.get(
        f"{BASE_URL}/v1/transactions/?page=1&page_size=10", headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        transactions = data["results"]
        print(
            f"✓ List transactions: Found {data['count']} total, showing {len(transactions)}"
        )
        for tx in transactions[:3]:  # Show first 3
            print(f"  - {tx['transaction_type']} {tx['amount']} {tx['asset_symbol']}")
    else:
        print(f"✗ List transactions failed: {response.status_code}")

    # Transaction stats
    response = requests.get(f"{BASE_URL}/v1/transactions/stats", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print("✓ Transaction stats:")
        print(f"  Total transactions: {stats['total_transactions']}")
        print(f"  Total volume: ${stats['total_volume_usd']:,.2f}")
        print(f"  24h transactions: {stats['transactions_24h']}")
    else:
        print(f"✗ Transaction stats failed: {response.status_code}")


def test_sse(token):
    """Test SSE endpoint (just check if it connects)"""
    print("\n=== Testing SSE Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}

    # Just test that we can connect to the SSE endpoint
    try:
        response = requests.get(
            f"{BASE_URL}/v1/portfolio/stream", headers=headers, stream=True, timeout=1
        )
        if response.status_code == 200:
            print("✓ SSE endpoint accessible")
            # Read just the first event
            for line in response.iter_lines():
                if line:
                    print(f"  Received event: {line.decode()[:100]}...")
                    break
        else:
            print(f"✗ SSE endpoint failed: {response.status_code}")
    except requests.exceptions.Timeout:
        print("✓ SSE endpoint connected (timeout expected)")
    except Exception as e:
        print(f"✗ SSE error: {e}")


def main():
    """Run all tests"""
    print("=== Portfolio Dashboard API Tests ===")
    print(f"Testing against: {BASE_URL}")

    # Test authentication
    token = test_auth()
    if not token:
        print("\nAuthentication failed. Cannot continue tests.")
        return

    # Test other endpoints
    test_wallets(token)
    test_portfolio(token)
    test_transactions(token)
    test_sse(token)

    print("\n=== Tests Complete ===")


if __name__ == "__main__":
    main()
