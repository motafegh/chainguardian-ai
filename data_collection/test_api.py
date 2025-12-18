import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ETHERSCAN_API_KEY', '')

print(f"🔑 Testing Etherscan API Key...")
print(f"   Key: {api_key[:6]}...{api_key[-4:] if len(api_key) > 10 else 'INVALID'}")

# Test with known good contract (recent, verified)
test_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

params = {
    'module': 'contract',
    'action': 'getsourcecode',
    'address': test_address,
    'apikey': api_key
}

response = requests.get("https://api.etherscan.io/api", params=params)
data = response.json()

print(f"\n📊 API Response:")
print(f"   Status: {data.get('status')}")
print(f"   Message: {data.get('message')}")
print(f"   Result: {data.get('result', 'N/A')[:100]}...")

if data['status'] == '1':
    print(f"\n✅ API KEY WORKS!")
    result = data['result'][0]
    print(f"   Contract: {result.get('ContractName', 'Unknown')}")
    print(f"   Verified: {'Yes' if result.get('SourceCode') else 'No'}")
else:
    print(f"\n❌ API KEY ISSUE!")
    print(f"   Error: {data.get('result', 'Unknown error')}")
    print(f"\n💡 POSSIBLE CAUSES:")
    print(f"   1. Invalid API key")
    print(f"   2. API key not activated")
    print(f"   3. Rate limit exceeded")
    print(f"   4. Network issue")
