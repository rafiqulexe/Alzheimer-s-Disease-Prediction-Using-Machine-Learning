import sys
import os
import subprocess
from pathlib import Path

# Automatically switch to local .venv if run using global Python
BASE_DIR = Path(__file__).resolve().parent
venv_python = BASE_DIR / ".venv" / "Scripts" / "python.exe"
if venv_python.exists() and sys.executable.lower() != str(venv_python).lower():
    sys.exit(subprocess.call([str(venv_python)] + sys.argv))

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print("\n" + "=" * 56)
    print("  Alzheimer's Detection & Assistant Web Server")
    print(f"  URL: http://{host}:{port}")
    print("=" * 56 + "\n")
    uvicorn.run("app:app", host=host, port=port, reload=True)
