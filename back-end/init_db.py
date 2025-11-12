import sqlite3

# connect to (or create) the database file
conn = sqlite3.connect("skillpath.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    country TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    question_text TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS options (
    options_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    option_text TEXT NOT NULL,
    score INTEGER NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS careers (
    career_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS career_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    career_id TEXT NOT NULL,
    resource_type TEXT CHECK(resource_type IN ('course','project')) NOT NULL,
    resource_name TEXT NOT NULL,
    FOREIGN KEY (career_id) REFERENCES careers(career_id) ON DELETE CASCADE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS career_category_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    career_id TEXT NOT NULL,
    category TEXT NOT NULL,
    FOREIGN KEY (career_id) REFERENCES careers(career_id) ON DELETE CASCADE
);
""")

print("✅ Tables created successfully!")

# commit and close
conn.commit()
conn.close()
