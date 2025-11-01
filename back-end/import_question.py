import sqlite3
import csv

# Filenames (change if yours are different)
QUESTIONS_CSV = "questions_with_category_and_idoriginal.csv"
OPTIONS_CSV = "options_with_scores^LLL (1).csv"
CAREERS_CSV = "career.csv"
RESOURCES_CSV = "career_resource.csv"
MAPPINGS_CSV = "career_mapping_category.csv"

# Connect to database
conn = sqlite3.connect("skillpath.db")
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

# ---------------------------------------------------------
# Clear old data so we don’t get duplicate ID errors
# ---------------------------------------------------------
cur.execute("DELETE FROM options")
cur.execute("DELETE FROM questions")
cur.execute("DELETE FROM career_resources")
cur.execute("DELETE FROM career_category_mapping")
cur.execute("DELETE FROM careers")
conn.commit()

# ---------------------------------------------------------
# Import Questions
# ---------------------------------------------------------
q_count = 0
with open(QUESTIONS_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("""
            INSERT OR IGNORE INTO questions (question_id, category, question_text) 
            VALUES (?, ?, ?)
        """, (row["question_id"], row["category"], row["question_text"]))
        q_count += 1

# ---------------------------------------------------------
# Import Options
# ---------------------------------------------------------
o_count = 0
with open(OPTIONS_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Score might be "2" or "2.0" in CSV; store as int
        try:
            score_val = int(float(row["score"]))
        except:
            score_val = 0
        cur.execute("""
            INSERT OR IGNORE INTO options (options_id, question_id, option_text, score) 
            VALUES (?, ?, ?, ?)
        """, (int(row["options_id"]), row["question_id"], row["option_text"], score_val))
        o_count += 1

# ---------------------------------------------------------
# Import Careers
# ---------------------------------------------------------
c_count = 0
with open(CAREERS_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cid = str(row["career_id"]).strip()  # store as TEXT
        name = (row["career_name"]).strip()
        desc = (row["description"]).strip()
        cur.execute("""
            INSERT OR IGNORE INTO careers (career_id, name, description)
            VALUES (?, ?, ?)
        """, (cid, name, desc))
        c_count += 1

# ---------------------------------------------------------
# Import Career -> Category Mappings
# ---------------------------------------------------------
m_count = 0
with open(MAPPINGS_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cid = str(row["career_id"]).strip()
        category = (row["category"]).strip()
        cur.execute("""
            INSERT INTO career_category_mapping (career_id, category)
            VALUES (?, ?)
        """, (cid, category))
        m_count += 1

# ---------------------------------------------------------
# Import Career Resources
# CSV header: id,career_id,resource_type,resource_name
# DB table: career_resources(id INTEGER PK AUTOINCREMENT, career_id TEXT, resource_type TEXT CHECK('course'/'project'), resource_name TEXT)
# We ignore the CSV id and let DB assign one. We also lowercase resource_type to satisfy the CHECK.
# ---------------------------------------------------------
r_count = 0
with open(RESOURCES_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cid = str(row["career_id"]).strip()
        rtype = (row["resource_type"]).strip().lower()
        rname = (row["resource_name"]).strip()
        cur.execute("""
            INSERT INTO career_resources (career_id, resource_type, resource_name)
            VALUES (?, ?, ?)
        """, (cid, rtype, rname))
        r_count += 1

# Save and close
conn.commit()

# Quick counts to confirm
counts = {}
for table in ("questions", "options", "careers", "career_category_mapping", "career_resources"):
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    counts[table] = cur.fetchone()[0]

conn.close()

print("✅ Import completed successfully!")
print(f"- Questions: {q_count} rows (DB count: {counts['questions']})")
print(f"- Options:   {o_count} rows (DB count: {counts['options']})")
print(f"- Careers:   {c_count} rows (DB count: {counts['careers']})")
print(f"- Mappings:  {m_count} rows (DB count: {counts['career_category_mapping']})")
print(f"- Resources: {r_count} rows (DB count: {counts['career_resources']})")