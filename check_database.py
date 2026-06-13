import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Add new columns if they don't exist
try:
    cursor.execute("ALTER TABLE users ADD COLUMN branch TEXT;")
    print("Added column: branch")
except sqlite3.OperationalError:
    print("Column 'branch' already exists")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN year TEXT;")
    print("Added column: year")
except sqlite3.OperationalError:
    print("Column 'year' already exists")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN image TEXT DEFAULT 'default.png';")
    print("Added column: image")
except sqlite3.OperationalError:
    print("Column 'image' already exists")

conn.commit()
conn.close()


