"""
app.py — Project root launcher
================================
Run this file to start the application:
    python app.py
"""

import sys
from pathlib import Path
from runpy import run_path

# Path to the actual Streamlit application
app_path = Path(__file__).parent / "frontend" / "app.py"

if __name__ == "__main__":
    # Check if the process is already being run by Streamlit Cloud or the streamlit CLI
    is_streamlit = "streamlit" in sys.argv[0].lower()
    
    if not is_streamlit:
        # User ran `python app.py` -> Launch Streamlit subprocess
        import subprocess
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", "8501"],
            check=True,
        )
    else:
        # Streamlit Cloud ran `streamlit run app.py` -> Transparent passthrough
        run_path(str(app_path))
else:
    # If imported directly
    run_path(str(app_path))
