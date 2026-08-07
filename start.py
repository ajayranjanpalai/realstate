import os
import sys
import io

# Fix standard output encoding for Windows environment when printing unicode/emojis
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure real_estate_system directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_DIR = os.path.join(BASE_DIR, 'real_estate_system')
if SYSTEM_DIR not in sys.path:
    sys.path.insert(0, SYSTEM_DIR)

# Import run_server from server module
from frontend.server import run_server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Real Estate Web Service on port {port}...")
    run_server(port=port)
