#!/usr/bin/env python3
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import settings

# Check database
engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT symbol, market_cap, dividend_yield FROM stocks LIMIT 3"))
    print("Database contents:")
    for row in result:
        print(f"  {row[0]}: Market Cap={row[1]}, Dividend Yield={row[2]}")
