import sys
sys.path.insert(0, '/backend')

from backend.app.core.config import settings

print(f"DATABASE_URL: {settings.DATABASE_URL}")

# Now test the connection
import sqlite3
from pathlib import Path

# Extract the path from DATABASE_URL
url = settings.DATABASE_URL
if url.startswith("sqlite:///"):
    db_path = url.replace("sqlite:///", "")
    print(f"Database path: {db_path}")
    
    # Test connection
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, market_cap, dividend_yield FROM stocks LIMIT 1")
        row = cursor.fetchone()
        print(f"SQL query result: {row}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
