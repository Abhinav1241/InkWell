"""
Inkwell — Gemma Verification Script

Tests whether a real Gemma model is genuinely callable in this environment.
Per user instruction: if Gemma is not directly callable, we do NOT fake it with Flash;
we remove it and take Veo + Lyria only for bonuses.
"""

from __future__ import annotations

import sys
from backend import config

def test_gemma():
    from google import genai
    
    # Try different potential Gemma model IDs
    candidates = [
        "gemma-3-4b-it",
        "gemma-2-27b-it",
        "gemma-2-9b-it",
        "gemma-2-2b-it",
    ]
    
    print("Testing Gemma model availability...")
    client = genai.Client() # default client
    
    for model_id in candidates:
        try:
            print(f"Testing model: {model_id}")
            response = client.models.generate_content(
                model=model_id,
                contents="Classify: shotType=wide, characters=1. Answer: SIMPLE or COMPLEX.",
            )
            print(f"✓ Success with {model_id}! Response: {response.text}")
            return model_id
        except Exception as e:
            print(f"✗ Failed with {model_id}: {e}")
            
    print("\nNo Gemma model was directly callable via API in this environment.")
    return None

if __name__ == "__main__":
    result = test_gemma()
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
