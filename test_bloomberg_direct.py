"""
Test script for direct Bloomberg API connection (no server needed)
"""
import sys

print("=" * 60)
print("Direct Bloomberg API Connection Test")
print("=" * 60)

# Test 1: Import blpapi
print("\n1. Testing blpapi import...")
try:
    import blpapi
    print(f"   [OK] blpapi imported successfully")
    print(f"   [OK] Version: {blpapi.__version__}")
except ImportError as e:
    print(f"   [FAILED] {e}")
    sys.exit(1)

# Test 2: Import new Bloomberg client
print("\n2. Testing Bloomberg client import...")
try:
    from bain_abf_portal.models.bloomberg_client import BloombergClient, BloombergSpreadProvider
    print(f"   [OK] Bloomberg client imported successfully")
except ImportError as e:
    print(f"   [FAILED] {e}")
    sys.exit(1)

# Test 3: Test connection
print("\n3. Testing Bloomberg Terminal connection...")
try:
    client = BloombergClient()
    if client.is_available():
        print("   [OK] Bloomberg Terminal connection successful!")
        print("   [OK] No server needed - direct connection")
        
        # Test a simple data request
        print("\n4. Testing data retrieval...")
        try:
            # Try to get SOFR rate
            sofr = client.get_live_price("SOFRRATE Index")
            if sofr is not None:
                print(f"   [OK] Retrieved SOFR rate: {sofr}")
            else:
                print("   [WARNING] Could not retrieve SOFR (may need Bloomberg Terminal access)")
        except Exception as e:
            print(f"   [WARNING] Data retrieval test: {e}")
        
        client.close()
    else:
        print("   [WARNING] Bloomberg Terminal not running or not accessible")
        print("   [WARNING] Make sure Bloomberg Terminal is running with BBComm enabled")
except Exception as e:
    print(f"   [WARNING] Connection error: {e}")
    print("   [WARNING] This is normal if Bloomberg Terminal is not running")

# Test 4: Test spread provider
print("\n5. Testing BloombergSpreadProvider...")
try:
    provider = BloombergSpreadProvider()
    if provider.is_available():
        print("   [OK] Spread provider connected")
        print("   [OK] Ready to fetch structured credit spreads")
    else:
        print("   [WARNING] Spread provider not available (Bloomberg Terminal not running)")
except Exception as e:
    print(f"   [WARNING] Spread provider error: {e}")

print("\n" + "=" * 60)
print("Installation Summary:")
print("=" * 60)
print("[OK] blpapi is installed")
print("[OK] Direct Bloomberg client is ready")
print("\nKey differences from blpapi-mcp:")
print("- No server needed - connects directly to Bloomberg Terminal")
print("- Compatible with pandas 2.0+")
print("- Simpler setup - just need Bloomberg Terminal running")
print("\nNext steps:")
print("1. Make sure Bloomberg Terminal is running")
print("2. Run your Streamlit app - it will connect directly")
print("=" * 60)

