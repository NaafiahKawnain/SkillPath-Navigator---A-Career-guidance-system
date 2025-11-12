<h3>SkillPath Navigator</h3><br>
SkillPath Navigator is a lightweight offline web app that converts a short assessment and a brief self-description into clear, personalized career suggestions.  
It doesn’t just show job titles — it also suggests “what to do next” (recommended courses and project ideas) so users can start building skills immediately.

---

<h4>🧩 What It Is</h4><br>
A small full-stack system designed to run completely offline.
- **Backend:** Python (Flask) with SQLite database (`skillpath.db`)
- **Frontend:** HTML, CSS, JavaScript

---
<h4>🚀 Highlights</h4><br>
- 30-question assessment across 6 categories:
  - Logical Reasoning  
  - Creativity  
  - Technical Knowledge  
  - Communication Skills  
  - Time Management  
  - Problem Solving
- Lightweight keyword-based NLP that analyzes the user’s short “About Me” note
- Transparent scoring and category-based ranking
- Each career suggestion includes:
  - Description
  - Recommended courses
  - Project ideas

---
<h4>⚙️ How It Works</h4><br>
**Scoring logic:**
1. **Quiz**
   - Each category → 5 questions → options scored 1–3.
   - Per-category score normalized: `raw / 15`.
2. **NLP**
   - Scans the user note for simple keywords (e.g., “python”, “sql”, “design”).
   - Scores normalized by the highest hit → best category = 1.0.
3. **Final Blend**
   - If keywords found → `70% quiz + 30% NLP`
   - If none → `100% quiz`
4. **Career Ranking**
   - Fetch careers mapped to top-scoring categories.
   - Rank by total category score.
   - Attach courses/projects from the database.

**Example:**  
If Technical Knowledge quiz = 0.80 and NLP = 1.00 →  
`Final = 0.7 × 0.80 + 0.3 × 1.00 = 0.86`

---
<h4>🏗️ Architecture Overview</h4><br>
**Frontend:**  
`index.html` (welcome) → `assessment.html` (quiz) → `result.html` (suggestions)

**Backend (Flask):**
- Serves HTML + JSON APIs
- Implements scoring logic
- Manages SQLite DB operations

**Database (SQLite):**
- `questions`, `options`
- `careers`, `career_category_mappings`
- `resources` (courses & projects)

**APIs:**
| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET | `/api/questions` | Fetch quiz content |
| POST | `/api/submit` | Return category scores + career suggestions |
| GET | `/api/health` | Simple health check |
| POST | `/api/register` / `/api/login` | Minimal user system for demo |

---
<h4>🎯 Why This Approach</h4><br>
- **Explainable:** Simple weighted scoring, easy to trace and interpret  
- **Practical:** Career output includes concrete “next steps” — not just names  
- **Offline-first:** Fully self-contained (Flask + SQLite)

---

<h4>🧠 To Run Locally</h4><br>
```bash
cd back-end
pip install -r requirements.txt
python app.py
