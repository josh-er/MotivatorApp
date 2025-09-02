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
    ("Why do we feen Master Bruce? So we can chief that skrong. - Motivator",),
    ("Wax melts when heated so it can serve another purpose. Are you heated? - Motivator",),
    ("Jarvis, give this fella props because they're grinding for the life they want. - Motivator",),
    ("You can tell who really bout this Family Guy shit and who not. - Motivator",)
]

cursor.executemany("INSERT OR IGNORE INTO quotes (text) VALUES (?)", quotes)
conn.commit()
conn.close()

print("✅ quotes.db initialized and seeded.")
