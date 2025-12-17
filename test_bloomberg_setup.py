"""
Test script to verify Bloomberg API installation and setup
"""
import sys

print("=" * 60)
print("Bloomberg API Installation Test")
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

# Test 2: Import blpapi_mcp
print("\n2. Testing blpapi-mcp import...")
try:
    import blpapi_mcp
    print(f"   [OK] blpapi-mcp imported successfully")
except ImportError as e:
    print(f"   [FAILED] {e}")
    sys.exit(1)

# Test 3: Check if we can create a Bloomberg session (requires Terminal)
print("\n3. Testing Bloomberg connection...")
try:
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost("localhost")
    sessionOptions.setServerPort(8194)
    
    session = blpapi.Session(sessionOptions)
    
    if session.start():
        print("   [OK] Bloomberg Terminal connection successful!")
        print("   [OK] Session started")
        session.stop()
    else:
        print("   [WARNING] Bloomberg Terminal not running or not accessible")
        print("   [WARNING] Make sure Bloomberg Terminal is running with BBComm enabled")
except Exception as e:
    print(f"   [WARNING] Could not connect to Bloomberg Terminal: {e}")
    print("   [WARNING] This is normal if Bloomberg Terminal is not running")

# Test 4: Check blpapi-mcp server (if running)
print("\n4. Testing blpapi-mcp server...")
try:
    import requests
    response = requests.get("http://127.0.0.1:8000/health", timeout=2)
    if response.status_code == 200:
        print("   [OK] blpapi-mcp server is running!")
    else:
        print(f"   [WARNING] Server responded with status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("   [WARNING] blpapi-mcp server is not running")
    print("   [WARNING] To start it, run: python -m blpapi_mcp --sse --host 127.0.0.1 --port 8000")
except Exception as e:
    print(f"   [WARNING] Error checking server: {e}")

print("\n" + "=" * 60)
print("Installation Summary:")
print("=" * 60)
print("[OK] blpapi is installed and importable")
print("[OK] blpapi-mcp is installed and importable")
print("\nNext steps:")
print("1. Make sure Bloomberg Terminal is running")
print("2. Start the blpapi-mcp server:")
print("   python -m blpapi_mcp --sse --host 127.0.0.1 --port 8000")
print("3. Your Streamlit app should now be able to connect to Bloomberg")
print("=" * 60)

