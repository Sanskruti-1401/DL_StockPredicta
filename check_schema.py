import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(stocks)")
columns = cursor.fetchall()

print("Columns in stocks table:")
for col in columns:
    print(f"  {col[1]}: {col[2]}")

conn.close()
