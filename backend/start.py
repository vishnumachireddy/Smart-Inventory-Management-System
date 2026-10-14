import os
import sys
import traceback

# Force unbuffered output so all startup logs and errors appear in Render live tail
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

# Ensure current directory is in sys.path
curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

if __name__ == "__main__":
    raw_port = os.environ.get("PORT", "8000")
    try:
        port = int(raw_port)
    except (ValueError, TypeError):
        print(f"[StockSense] Warning: could not parse PORT '{raw_port}' as int. Falling back to 8000.", flush=True)
        port = 8000

    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[StockSense] Starting production server on {host}:{port} (PORT={raw_port})...", flush=True)

    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
    except Exception as exc:
        print(f"[StockSense CRITICAL ERROR] Failed to start server: {exc}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
