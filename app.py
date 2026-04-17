"""
app.py — Project root launcher
================================
Run this file to start the Streamlit application:
    streamlit run app.py
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).parent / "frontend" / "app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", "8501"],
        check=True,
    )
