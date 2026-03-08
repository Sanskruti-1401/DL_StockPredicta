import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute("SELECT symbol, market_cap, dividend_yield, pe_ratio FROM stocks LIMIT 3")
rows = cursor.fetchall()

print("Stock data:")
for row in rows:
    print(f"  {row[0]}: market_cap={row[1]}, dividend_yield={row[2]}, pe_ratio={row[3]}")

conn.close()
