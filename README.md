<h1>**SkillPath Navigator**</h1><br>
SkillPath Navigator is a small, offline web app that turns a short assessment plus a brief self‑description into clear, personalized career suggestions. It doesn’t just show job titles—it also attaches “what to do next” (courses and project ideas) so users can start building skills immediately.

<h2>**What it is**</h2><br>
A full‑stack, offline system:
Backend: Python (Flask) with an SQLite database (single file: skillpath.db)
Frontend: HTML, CSS, JavaScript

<h2>**Highlights**</h2><br>
30‑question assessment across six categories (Logical Reasoning, Creativity, Technical Knowledge, Communication Skills, Time Management, Problem Solving)
Lightweight keyword‑based NLP on a short “about me” note 
Transparent scoring and simple ranking of careers mapped to top categories
Each suggestion includes a brief description, courses, and project ideas

<h2>**How it works (scoring)**</h2><br>
Quiz: Each category has 5 questions, each option scored 1–3. Per‑category quiz score is normalized as a percentage by dividing raw/15 (0..1).
NLP: The note is scanned for simple category keywords (e.g., python, sql, design); matches are normalized by the highest hit so the best category becomes 1.0 (others 0..1).
Blend per category:
If keywords are found: final = 70% quiz + 30% NLP
If not: final = 100% quiz
Careers: Pick the user’s strongest categories → fetch careers mapped to those categories → rank by the sum of mapped category scores → attach courses/projects from the database.
Example (illustrative):
If Technical Knowledge quiz% = 0.80 and NLP% = 1.00, final = 0.7×0.80 + 0.3×1.00 = 0.86.

Architecture at a glance
Frontend (HTML/CSS/JS): index (welcome), assessment (quiz), result (suggestions)
Backend (Flask): serves pages and JSON APIs; implements scoring and career ranking
Database (SQLite): users, questions, options, careers, career‑category mappings, resources
Data model (conceptual)
Questions (question_id, category, text) → Options (option_text, score)
Careers (career_id, name, description)
Mappings (career_id ↔ category)
Resources (career_id ↔ course/project name)
APIs (brief)
GET /api/questions — quiz content
POST /api/submit — returns category scores, ranked careers, and resources
(Plus minimal register/login and a simple health check for local demos)

<h2>**Why this approach**</h2><br>
Explainable: simple percentages + a small keyword boost
Practical: recommendations include concrete next steps (courses, projects)
