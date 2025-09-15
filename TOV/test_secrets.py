#!/usr/bin/env python3
"""
Test script to verify secrets loading works correctly
"""
import os
from dotenv import load_dotenv

# Load .env for testing
load_dotenv()

def _get_secret(key: str, default: str = None) -> str:
    """Get secret from Streamlit secrets or environment variables with fallback."""
    try:
        import streamlit as st
        # Try Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    
    # Fallback to environment variables (for local development)
    return os.getenv(key, default)

print("=== Secrets Test ===")
print(f"OPENAI_API_KEY: {'✓ Set' if _get_secret('OPENAI_API_KEY') else '✗ Not set'}")
print(f"OPENAI_BASE_URL: {_get_secret('OPENAI_BASE_URL', 'https://api.openai.com/v1')}")
print(f"LLM_MODEL: {_get_secret('LLM_MODEL', 'gpt-4o')}")
print(f"LLM_TIMEOUT: {_get_secret('LLM_TIMEOUT', '20')}")

if _get_secret('OPENAI_API_KEY'):
    print(f"API Key (first 8 chars): {_get_secret('OPENAI_API_KEY')[:8]}...")
    print("\n✓ Secrets loading works correctly!")
else:
    print("\n✗ OPENAI_API_KEY not found!")
    print("Make sure you have either:")
    print("1. A .env file with OPENAI_API_KEY=your_key")
    print("2. Streamlit secrets configured")
