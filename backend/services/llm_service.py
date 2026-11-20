import os
import socket
import requests
from typing import Dict, Any, Optional

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


def is_ollama_port_open() -> bool:
    """Fast socket probe (0.1s) to avoid slow urllib3 retry loops when Ollama is offline."""
    try:
        # Parse port from OLLAMA_BASE_URL
        port = 11434
        host = "127.0.0.1"
        if ":" in OLLAMA_BASE_URL:
            parts = OLLAMA_BASE_URL.replace("http://", "").replace("https://", "").split(":")
            host = parts[0]
            if len(parts) > 1 and parts[1].isdigit():
                port = int(parts[1])

        with socket.create_connection((host, port), timeout=0.1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError, Exception):
        return False


def check_ollama_status() -> Dict[str, Any]:
    """Inspects the local Ollama daemon and checks for configured model presence."""
    if not is_ollama_port_open():
        return {
            "provider": LLM_PROVIDER,
            "base_url": OLLAMA_BASE_URL,
            "configured_model": OLLAMA_MODEL,
            "connected": False,
            "available_models": [],
            "model_available": False,
            "status_message": f"Ollama daemon is not reachable on {OLLAMA_BASE_URL}. Ensure Ollama is installed and running (`ollama serve`)."
        }

    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            model_found = any(OLLAMA_MODEL.lower() in m.lower() for m in models)
            return {
                "provider": LLM_PROVIDER,
                "base_url": OLLAMA_BASE_URL,
                "configured_model": OLLAMA_MODEL,
                "connected": True,
                "available_models": models,
                "model_available": model_found,
                "status_message": f"Connected to Ollama on {OLLAMA_BASE_URL}." + (
                    f" Model '{OLLAMA_MODEL}' is ready." if model_found else f" Model '{OLLAMA_MODEL}' not found. Available: {models}"
                )
            }
        else:
            return {
                "provider": LLM_PROVIDER,
                "base_url": OLLAMA_BASE_URL,
                "configured_model": OLLAMA_MODEL,
                "connected": False,
                "available_models": [],
                "model_available": False,
                "status_message": f"Ollama daemon responded with HTTP {resp.status_code}."
            }
    except Exception as e:
        return {
            "provider": LLM_PROVIDER,
            "base_url": OLLAMA_BASE_URL,
            "configured_model": OLLAMA_MODEL,
            "connected": False,
            "available_models": [],
            "model_available": False,
            "status_message": f"Cannot connect to Ollama at {OLLAMA_BASE_URL}: {str(e)}"
        }


def query_llm(prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """Queries Ollama if available; returns structured status."""
    status = check_ollama_status()
    if not status["connected"] or not status["model_available"]:
        return {
            "success": False,
            "llm_used": False,
            "response": None,
            "error": status["status_message"],
            "setup_guide": "To enable local LLM: 1) Download Ollama from https://ollama.com. 2) Run `ollama run llama3.2`. 3) Verify at http://127.0.0.1:11434."
        }

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 400,
                "temperature": 0.2
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=2.0)
        if resp.status_code == 200:
            result = resp.json().get("response", "")
            return {
                "success": True,
                "llm_used": True,
                "response": result.strip(),
                "error": None
            }
        else:
            return {
                "success": False,
                "llm_used": False,
                "response": None,
                "error": f"Ollama API error {resp.status_code}: {resp.text}"
            }
    except Exception as err:
        return {
            "success": False,
            "llm_used": False,
            "response": None,
            "error": f"Ollama execution error: {str(err)}"
        }
