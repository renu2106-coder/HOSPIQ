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
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")

    print("\n" + "=" * 65)
    print("  HOSPIQ: Hospital Information & Quality Intelligence System")
    print("  Unified Single-Command Server (Frontend + Backend)")
    print("=" * 65)
    print(f"  [>] Web Application:  http://{host}:{port}")
    print(f"  [>] API Docs:         http://{host}:{port}/docs")
    print("=" * 65)

    if not os.getenv("PORT"):
        print("  Opening browser automatically...\n")
        threading.Thread(target=open_browser_tab, daemon=True).start()

    # Serve the full unified application
    uvicorn.run("backend.main:app", host=host, port=port, log_level="info")

