import os
import re
import sqlite3
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "skillpath.db")  # absolute path to DB
FRONT_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "front-end"))

app = Flask(__name__)
CORS(app)

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# ===== Category/NLP/mapping helpers =====
CATEGORIES = [
    "Logical Reasoning",
    "Creativity",
    "Technical Knowledge",
    "Communication Skills",
    "Time Management",
    "Problem Solving",
]

KEYWORDS_BY_CATEGORY = {
    "Logical Reasoning": ["logic", "puzzle", "reason", "pattern", "analytical", "algorithm", "deduction"],
    "Creativity": ["creative", "design", "idea", "invent", "innovate", "imagine", "prototype", "art", "ui", "ux", "story", "concept"],
    "Technical Knowledge": ["code", "coding", "program", "python", "java", "c++", "javascript", "sql", "algorithms", "systems", "backend", "frontend", "api", "database","Machine Learning","Artificial Intelligence"],
    "Communication Skills": ["communicate", "communication", "present", "presentation", "explain", "write", "writing", "document", "documentation", "collaborate", "team", "stakeholder", "negotiate", "speak", "meeting", "feedback"],
    "Time Management": ["deadline", "schedule", "prioritize", "priority", "plan", "planning", "organize", "time", "multitask", "productivity"],
    "Problem Solving": ["solve", "solution", "troubleshoot", "debug", "issue", "fix", "root cause", "analysis", "approach", "strategy", "optimize"],
}

def _pattern_for_kw(kw: str) -> str:
    """
    Build a regex that matches a keyword with common English endings.
    - If it's a phrase (has a space), match exactly as a whole phrase.
    - If it's a single word, allow common suffixes: e, s, ed, ing, ive, ivity, al, ally
    """
    kw = kw.strip().lower()
    if " " in kw:
        # phrase → match the whole phrase
        return r"\b" + re.escape(kw) + r"\b"

    # Generic endings for most verbs/nouns (create/creative/creating/creativity, etc.)
    stem = kw[:-1] if kw.endswith("e") else kw  # drop trailing e for ing/ed forms
    endings = "(?:e|es|ed|er|ers|ing|ive|ivity|al|ally|is|tics|tical)?"
    return rf"\b{re.escape(stem)}{endings}\b"


# Simple normalization (since every category has 5 questions, max score per Q = 3)
QUESTIONS_PER_CATEGORY = 5
MAX_SCORE_PER_QUESTION = 3
QUIZ_MAX_PER_CATEGORY = QUESTIONS_PER_CATEGORY * MAX_SCORE_PER_QUESTION  # 15

def quiz_category_scores(answers_dict):
    """Sum selected option scores per category using your questions table."""
    scores = {}
    for qid, selected_score in (answers_dict or {}).items():
        row = query_db("SELECT category FROM questions WHERE question_id=?", (qid,), one=True)
        if not row:
            continue
        cat = row[0]
        try:
            sc = int(selected_score)
        except Exception:
            sc = 0
        scores[cat] = scores.get(cat, 0) + sc
    return scores

def nlp_category_scores(text):
    """Keyword-based scoring with basic morphological matching; returns 0..1 per category."""
    txt = re.sub(r"[^a-z0-9\s]", " ", str(text).lower())
    scores = {}
    for cat, kws in KEYWORDS_BY_CATEGORY.items():
        s = 0
        for kw in kws:
            pattern = _pattern_for_kw(kw)
            matches = re.findall(pattern, txt)
            # Weight phrases a bit higher (keywords with a space in original kw)
            s += (len(matches) * (2 if " " in kw else 1))
        scores[cat] = s

    max_nlp = max(scores.values()) if any(scores.values()) else 1
    return {k: (v / max_nlp) for k, v in scores.items()}  # 0..1

def blend_scores(quiz_norm, nlp_norm, w_quiz=0.7, w_nlp=0.3):
    cats = set(quiz_norm) | set(nlp_norm)
    return {c: w_quiz * quiz_norm.get(c, 0) + w_nlp * nlp_norm.get(c, 0) for c in cats}

def suggest_careers_from_categories(cat_scores, top_categories=2, limit=5, include_resources=True):
    """Pick top categories, fetch careers mapped to them, rank by summed category score, include resources."""
    top = sorted(cat_scores.items(), key=lambda x: x[1], reverse=True)[:top_categories]
    wanted = [c for c, s in top if s > 0]
    if not wanted:
        return [], []

    placeholders = ",".join("?" * len(wanted))
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(f"""
        SELECT c.career_id, c.name, c.description, m.category
        FROM career_category_mapping m
        JOIN careers c ON c.career_id = m.career_id
        WHERE m.category IN ({placeholders})
    """, tuple(wanted))
    rows = cur.fetchall()

    # Score each career by adding its categories' scores
    career_scores = {}
    details = {}
    for cid, name, desc, cat in rows:
        details[cid] = {"career_id": cid, "name": name, "description": desc}
        career_scores[cid] = career_scores.get(cid, 0) + cat_scores.get(cat, 0)

    ranked = sorted(career_scores.items(), key=lambda x: x[1], reverse=True)
    top_ids = [cid for cid, _ in ranked[:limit]]

    # Attach resources
    res_map = {}
    if include_resources and top_ids:
        placeholders2 = ",".join("?" * len(top_ids))
        cur.execute(f"""
            SELECT career_id, resource_type, resource_name
            FROM career_resources
            WHERE career_id IN ({placeholders2})
            ORDER BY resource_type, resource_name
        """, tuple(top_ids))
        for cid, rtype, rname in cur.fetchall():
            res_map.setdefault(cid, []).append({"type": rtype, "name": rname})

    conn.close()

    career_details = []
    for cid, sc in ranked[:limit]:
        d = details[cid]
        career_details.append({
            "career_id": cid,
            "name": d["name"],
            "description": d["description"],
            "score": round(sc, 3),
            "resources": res_map.get(cid, [])
        })
    names = [d["name"] for d in career_details]
    return names, career_details

# ===== Serve front-end via Flask =====

@app.route("/")
def root():
    # Serve index.html by default
    return send_from_directory(FRONT_DIR, "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONT_DIR, filename)

# ===== API routes =====

@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json(force=True)
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        phone = data.get("phone")
        country = data.get("country")

        if not (username and password and email and phone):
            return jsonify({"error": "Missing fields"}), 400

        phone_val = str(phone).strip()
        if not phone_val.isdigit():
            return jsonify({"error": "Phone must be digits only"}), 400

        # check duplicates
        if query_db("SELECT 1 FROM users WHERE username=? OR email=?", (username, email), one=True):
            return jsonify({"error": "Username or email already exists"}), 400

        query_db(
            "INSERT INTO users (username, password, email, phone, country) VALUES (?, ?, ?, ?, ?)",
            (username, password, email, phone_val, country),
        )
        return jsonify({"message": "User registered successfully"}), 201

    except Exception:
        tb = traceback.format_exc()
        print("REGISTER ERROR\n", tb)
        return jsonify({"error": "Server error", "detail": str(tb)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        username = data.get("username")
        password = data.get("password")
        if not (username and password):
            return jsonify({"error": "Missing credentials"}), 400

        user = query_db(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username , password), one=True
        )
        if user:
            return jsonify({"message": "Login successful"}), 200
        return jsonify({"error": "Invalid username or password"}), 401
    except Exception:
        tb = traceback.format_exc()
        print("LOGIN ERROR\n", tb)
        return jsonify({"error": "Server error", "detail": str(tb)}), 500

@app.route("/api/questions", methods=["GET"])
def get_questions():
    try:
        questions = query_db("SELECT question_id, category, question_text FROM questions")
        data = []
        for q in questions:
            qid, category, text = q
            options = query_db("SELECT options_id, option_text, score FROM options WHERE question_id=?", (qid,))
            data.append({
                "question_id": qid,
                "category": category,
                "text": text,
                "options": [{"id": o[0], "text": o[1], "score": o[2]} for o in options]
            })
        return jsonify(data)
    except Exception:
        tb = traceback.format_exc()
        print("QUESTIONS ERROR\n", tb)
        return jsonify({"error": "Server error", "detail": str(tb)}), 500

@app.route("/api/submit", methods=["POST"])
def submit():
    try:
        data = request.get_json(force=True) or {}

        # Accept both formats:
        #  - { "answers": { "QID": score, ... }, "text": "..." }
        #  - { "QID": score, ..., "text": "..." }
        if "answers" in data:
            answers = data.get("answers") or {}
            free_text = str(data.get("text", "")).strip()
        else:
            answers = {k: v for k, v in data.items() if k != "text"}
            free_text = str(data.get("text", "")).strip()

        # 1) Quiz scores per category (raw)
        quiz_scores = quiz_category_scores(answers)
        quiz_sorted = sorted(quiz_scores.items(), key=lambda x: x[1], reverse=True)

        # 2) Normalize quiz to 0..1 using fixed max (5 questions * 3 max per question = 15)
        quiz_norm = {cat: (score / QUIZ_MAX_PER_CATEGORY) for cat, score in quiz_scores.items()}

        # 3) NLP scores (0..1)
        nlp_norm = nlp_category_scores(free_text) if free_text else {c: 0 for c in CATEGORIES}
        nlp_sorted = sorted(nlp_norm.items(), key=lambda x: x[1], reverse=True)

        # 4) Weights: ignore NLP if no signal
        nlp_has_signal = any(v > 0 for v in nlp_norm.values()) if free_text else False
        w_quiz, w_nlp = (0.7, 0.3) if nlp_has_signal else (1.0, 0.0)

        # 5) Blend
        final_scores = blend_scores(quiz_norm, nlp_norm, w_quiz=w_quiz, w_nlp=w_nlp)
        final_sorted = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

        # 6) Careers from DB mapping
        career_names, career_details = suggest_careers_from_categories(final_scores, top_categories=2, limit=5)

        return jsonify({
            "quiz_scores": quiz_sorted,     # raw totals per category
            "quiz_norm": sorted(quiz_norm.items(), key=lambda x: x[1], reverse=True),  # 0..1
            "nlp_scores": nlp_sorted,       # 0..1
            "final_scores": final_sorted,   # 0..1 blended
            "careers": career_names,
            "career_details": career_details,
            "nlp_used": bool(nlp_has_signal),
            "weights": {"quiz": w_quiz, "nlp": w_nlp}
        }), 200

    except Exception:
        tb = traceback.format_exc()
        print("SUBMIT ERROR\n", tb)
        return jsonify({"error": "Server error", "detail": str(tb)}), 500

@app.route("/api/health")
def health():
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users','questions','options')")
        have = [r[0] for r in cur.fetchall()]
        conn.close()
        return jsonify({
            "ok": True,
            "db_path": DB_NAME,
            "db_exists": os.path.exists(DB_NAME),
            "tables_present": have
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ===== Auto-start (dev vs. silent) =====
if __name__ == "__main__":
    import sys, threading, time, webbrowser

    # Ensure working directory is the app folder
    os.chdir(BASE_DIR)

    port = int(os.getenv("PORT", "5000"))

    def open_browser():
        time.sleep(0.6)
        try:
            webbrowser.open_new_tab(f"http://127.0.0.1:{port}/index.html")
        except Exception:
            pass

    # Silent mode (pythonw/Waitress): open once and serve
    if sys.executable.lower().endswith("pythonw.exe"):
        threading.Thread(target=open_browser, daemon=True).start()
        try:
            from waitress import serve  # pip install waitress
            serve(app, host="127.0.0.1", port=port)
        except Exception:
            app.run(host="127.0.0.1", port=port)

    else:
        # Dev mode: only open once in the reloader child to avoid double-open
        debug = True
        if debug:
            if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
                threading.Thread(target=open_browser, daemon=True).start()
            app.run(host="127.0.0.1", port=port, debug=True)
        else:
            threading.Thread(target=open_browser, daemon=True).start()
            app.run(host="127.0.0.1", port=port, debug=False)