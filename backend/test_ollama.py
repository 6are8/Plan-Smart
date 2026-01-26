import requests
import os

ollama_url = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
model = os.getenv('OLLAMA_MODEL', 'llama3:latest')

print(f"Testing Ollama at: {ollama_url}")
print(f"Using model: {model}")
print("-" * 60)

# Test 1: Version
print("\n1️⃣ Testing /api/version...")
try:
    response = requests.get(f"{ollama_url}/api/version", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Generate
print("\n2️⃣ Testing /api/generate...")
try:
    payload = {
        "model": model,
        "prompt": "Say hello in German",
        "stream": False
    }
    response = requests.post(
        f"{ollama_url}/api/generate",
        json=payload,
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response: {data.get('response', 'N/A')[:100]}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: List models
print("\n3️⃣ Available models...")
try:
    response = requests.get(f"{ollama_url}/api/tags", timeout=5)
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        print(f"   Found {len(models)} models:")
        for m in models:
            print(f"     - {m.get('name')}")
    else:
        print(f"   Status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)