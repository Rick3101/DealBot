#!/usr/bin/env python3
"""
Simple connectivity test that forces IPv4 and disables SSL verification
"""

import os
import requests
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api():
    print("=== Simple API Test ===")
    
    # Force IPv4 by monkey patching
    original_getaddrinfo = socket.getaddrinfo
    def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    
    socket.getaddrinfo = ipv4_only_getaddrinfo
    
    try:
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            print("[FAIL] No bot token found")
            return False
        
        # Test with minimal SSL verification
        session = requests.Session()
        session.verify = True  # Keep SSL verification enabled
        
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        print(f"Testing URL: {url[:50]}...")
        
        response = session.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"[OK] Bot is working!")
                print(f"Bot name: {bot_info.get('first_name', 'Unknown')}")
                print(f"Bot username: @{bot_info.get('username', 'Unknown')}")
                return True
            else:
                print(f"[FAIL] API Error: {data.get('description', 'Unknown')}")
                return False
        else:
            print(f"[FAIL] HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("[FAIL] Request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[FAIL] Connection error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    finally:
        socket.getaddrinfo = original_getaddrinfo

if __name__ == "__main__":
    test_api()