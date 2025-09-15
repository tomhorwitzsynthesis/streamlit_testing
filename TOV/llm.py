"""
llm.py — minimal, provider-agnostic wrapper around an OpenAI-compatible Chat Completions API.

Goals for POC:
- One sync function: generate(system, user, *, model=None, params=None)
- Uses environment variables: OPENAI_API_KEY (required), OPENAI_BASE_URL (optional), LLM_MODEL (optional default)
- Targets the /v1/chat/completions endpoint; works with OpenAI and compatible providers.
- Simple retry (1) and timeout.
"""
from __future__ import annotations

import os
import time
import json
from typing import Dict, Any, Optional, Tuple
import requests
from dotenv import load_dotenv

# Try to load environment variables from .env file (for local development)
try:
    load_dotenv()
except:
    pass  # .env file not found, will use Streamlit secrets

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

DEFAULT_MODEL = _get_secret("LLM_MODEL", "gpt-4o")
BASE_URL = _get_secret("OPENAI_BASE_URL", "https://api.openai.com/v1")
API_KEY = _get_secret("OPENAI_API_KEY")
TIMEOUT_SECONDS = float(_get_secret("LLM_TIMEOUT", "20"))


def _estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 characters per token for English text."""
    return len(text) // 4


def _truncate_text(text: str, max_tokens: int) -> str:
    """Truncate text to fit within token limit, preserving word boundaries."""
    estimated_tokens = _estimate_tokens(text)
    if estimated_tokens <= max_tokens:
        return text
    
    # Calculate target character length (rough estimate)
    target_chars = max_tokens * 4
    if len(text) <= target_chars:
        return text
    
    # Truncate and find last complete word
    truncated = text[:target_chars]
    last_space = truncated.rfind(' ')
    if last_space > target_chars * 0.8:  # Only use word boundary if it's not too far back
        truncated = truncated[:last_space]
    
    return truncated + "..."


class LLMError(RuntimeError):
    pass


def _headers() -> Dict[str, str]:
    if not API_KEY:
        raise LLMError("OPENAI_API_KEY is not set")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def _request(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    resp = requests.post(url, headers=_headers(), json=payload, timeout=TIMEOUT_SECONDS)
    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise LLMError(f"LLM HTTP {resp.status_code}: {detail}")
    return resp.json()


def generate(system: str, user: str, *, model: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return dict with keys: text, model, usage, latency_s.

    Params may include: temperature, max_tokens, frequency_penalty, presence_penalty, top_p (optional).
    """
    # Get max_tokens from params or use default
    max_tokens = 400
    if params and "max_tokens" in params:
        max_tokens = params["max_tokens"]
    
    # Estimate total tokens and truncate if necessary
    # Reserve ~1000 tokens for response and system overhead
    max_input_tokens = 7000  # Conservative limit for gpt-4 (8192 - 1000 - 192)
    
    total_estimated = _estimate_tokens(system) + _estimate_tokens(user)
    if total_estimated > max_input_tokens:
        # Truncate user message first (usually the longer one)
        user_tokens = _estimate_tokens(user)
        system_tokens = _estimate_tokens(system)
        
        if user_tokens > system_tokens:
            # Truncate user message
            available_for_user = max_input_tokens - system_tokens
            user = _truncate_text(user, available_for_user)
        else:
            # Truncate system message
            available_for_system = max_input_tokens - user_tokens
            system = _truncate_text(system, available_for_system)
    
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.35,
        "max_tokens": max_tokens,
    }
    if params:
        # Only include allowed numeric params to avoid API errors
        for k in ("temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"):
            if k in params:
                payload[k] = params[k]

    # One retry with simple backoff
    t0 = time.time()
    try:
        data = _request(payload)
    except Exception as e:
        time.sleep(0.8)
        data = _request(payload)
    latency = time.time() - t0

    # Extract first choice
    try:
        choice = data["choices"][0]
        text = choice["message"]["content"].strip()
    except Exception as e:
        raise LLMError(f"Malformed LLM response: {data}")

    usage = data.get("usage", {})
    model_used = data.get("model", payload["model"]) or payload["model"]

    return {
        "text": text,
        "model": model_used,
        "usage": usage,
        "latency_s": round(latency, 3),
        "raw": data,
    }
