import sqlite3

conn = sqlite3.connect("quotes.db")
cursor = conn.cursor()

# Create the quotes table
cursor.execute("""
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL UNIQUE
)
""")

# Add starter quotes (UNIQUE ensures no duplicates)
quotes = [
    ("You've got this.",),
    ("Keep going. You're closer than you think.",),
    ("Small steps add up.",),
    ("Consistency > intensity.",),
    ("You can tell who really bout this Family Guy shit and who not.",)
]

cursor.executemany("INSERT OR IGNORE INTO quotes (text) VALUES (?)", quotes)
conn.commit()
conn.close()

print("✅ quotes.db initialized and seeded.")
