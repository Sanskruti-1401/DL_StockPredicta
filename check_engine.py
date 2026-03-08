import sys
sys.path.insert(0, '/backend')
from backend.app.db.base import engine
import sqlite3

print(f"Engine URL: {engine.url}")

# For SQLite, the URL database component is the file path
db_file = str(engine.url.database)
print(f"Database file from URL: {db_file}")

# Check if it's a relative path and resolve it
from pathlib import Path
if db_file and not Path(db_file).is_absolute():
    # Resolve relative to current working directory
    resolved_path = Path.cwd() / db_file
    print(f"Resolved to: {resolved_path}")
    print(f"Exists: {resolved_path.exists()}")
    
    # Query it to check the content
    if resolved_path.exists():
        conn = sqlite3.connect(str(resolved_path))
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, market_cap, dividend_yield FROM stocks LIMIT 1")
        row = cursor.fetchone()
        print(f"  Data: {row}")
        conn.close()
