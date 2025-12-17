"""
Comprehensive test to verify Bloomberg Terminal is actually connected and working
"""
import sys
from datetime import datetime

print("=" * 70)
print("Bloomberg Terminal Connection Verification")
print("=" * 70)
print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test 1: Import and create client
print("1. Creating Bloomberg client...")
try:
    from bain_abf_portal.models.bloomberg_client import BloombergClient, BLOOMBERG_TICKERS
    client = BloombergClient()
    print("   [OK] Client created")
except Exception as e:
    print(f"   [FAILED] {e}")
    sys.exit(1)

# Test 2: Check connection
print("\n2. Testing connection to Bloomberg Terminal...")
try:
    is_connected = client.is_available()
    if is_connected:
        print("   [OK] Connection successful")
        print(f"   [INFO] Session active: {client.session is not None}")
        if client.session:
            print(f"   [INFO] Session state: {client.session}")
    else:
        print("   [FAILED] Cannot connect to Bloomberg Terminal")
        print("   [INFO] Make sure Bloomberg Terminal is running with BBComm enabled")
        sys.exit(1)
except Exception as e:
    print(f"   [FAILED] Connection error: {e}")
    sys.exit(1)

# Test 3: Try to retrieve multiple securities to verify it's real
print("\n3. Testing data retrieval (this proves it's actually connected)...")
test_securities = [
    ("SOFR", "SOFRRATE Index"),
    ("UST 10Y", "USGG10YR Index"),
    ("UST 2Y", "USGG2YR Index"),
]

results = {}
for name, ticker in test_securities:
    try:
        print(f"\n   Testing {name} ({ticker})...")
        price = client.get_live_price(ticker)
        if price is not None:
            results[name] = price
            print(f"   [OK] {name}: {price}")
        else:
            print(f"   [WARNING] {name}: No data returned")
    except Exception as e:
        print(f"   [ERROR] {name}: {e}")

# Test 4: Try reference data request (more comprehensive)
print("\n4. Testing reference data request (multiple fields)...")
try:
    df = client.get_reference_data(
        ["SOFRRATE Index", "USGG10YR Index"],
        ["PX_LAST", "YLD_YTM_MID"]
    )
    if df is not None and not df.empty:
        print("   [OK] Reference data retrieved successfully")
        print(f"   [INFO] Retrieved {len(df)} securities")
        print("\n   Data retrieved:")
        print(df.to_string())
    else:
        print("   [WARNING] No reference data returned")
except Exception as e:
    print(f"   [ERROR] Reference data error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Verify session is still active
print("\n5. Verifying session is still active...")
try:
    if client.session:
        print("   [OK] Session is still active")
        print(f"   [INFO] Session object: {type(client.session)}")
    else:
        print("   [WARNING] Session is None")
except Exception as e:
    print(f"   [ERROR] Session check failed: {e}")

# Summary
print("\n" + "=" * 70)
print("Connection Verification Summary")
print("=" * 70)
if results:
    print("[OK] Successfully retrieved live data from Bloomberg Terminal:")
    for name, value in results.items():
        print(f"   - {name}: {value}")
    print("\n[CONFIRMED] Bloomberg Terminal is connected and working!")
    print("The connection is REAL and retrieving actual market data.")
else:
    print("[WARNING] Could not retrieve data - connection may not be fully working")
    print("Check that Bloomberg Terminal has proper data permissions.")

# Cleanup
try:
    client.close()
    print("\n[OK] Connection closed cleanly")
except Exception:
    pass

print("=" * 70)

