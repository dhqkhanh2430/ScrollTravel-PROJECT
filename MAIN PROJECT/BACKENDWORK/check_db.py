import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Check table structure
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables: {tables}")

# Count users
cursor.execute('SELECT COUNT(*) FROM users')
count = cursor.fetchone()[0]
print(f'Total users in database: {count}')

# Show all users
cursor.execute('SELECT username, email, phone FROM users')
rows = cursor.fetchall()
for row in rows:
    print(f'  User: {row[0]}, Email: {row[1]}, Phone: {row[2]}')

conn.close()
