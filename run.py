import os
import sys
import time
import threading
import webbrowser
import uvicorn

def open_browser_tab():
    time.sleep(1.2)
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  HOSPIQ: Hospital Information & Quality Intelligence System")
    print("  Unified Single-Command Server (Frontend + Backend)")
    print("=" * 65)
    print("  [>] Web Application:  http://127.0.0.1:8000")
    print("  [>] API Docs:         http://127.0.0.1:8000/docs")
    print("=" * 65)
    print("  Opening browser automatically...\n")

    threading.Thread(target=open_browser_tab, daemon=True).start()

    # Serve the full unified application
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, log_level="info")

